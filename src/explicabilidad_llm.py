import os
import json

class GeneradorExplicabilidad:
    """
    Persona 4: Módulo de Explicabilidad e Interfaz LLM.
    Convierte las métricas y decisiones algorítmicas del Agente IA 
    en justificaciones claras y legibles en lenguaje natural.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        # Intentar inicializar el cliente oficial de Gemini (google-genai)
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Aviso LLM] No se pudo inicializar la librería de Gemini: {e}")

    def generar_explicacion_decision(self, pedido, decision_ia, clima="normal", trafico="normal"):
        """Genera una justificación en lenguaje natural para la aceptación/rechazo de un pedido."""
        pago = pedido.get("pago_mxn", 0)
        distancia = pedido.get("distancia_km", 0)
        tiempo = pedido.get("tiempo_est_min", 0)
        estatus = decision_ia.get("decisión", "DESCONOCIDO")
        razon = decision_ia.get("razón", "")
        
        prompt = f"""
Eres un asistente inteligente para repartidores de plataforma. 
Explica en 2 oraciones breves y empáticas por qué la IA tomó la siguiente decisión:

- Estado de la Decisión: {estatus}
- Razón Heurística: {razon}
- Detalles del Pedido: Pago ${pago} MXN, Distancia {distancia} km, Tiempo Estimado {tiempo} min.
- Imprevistos Contextuales: Clima {clima}, Tráfico {trafico}.

Responde directo al repartidor en español.
"""
        # Intentar respuesta vía API de Gemini
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                return response.text.strip()
            except Exception as e:
                pass  # Fallback si falla la llamada API

        # Fallback en reglas deterministas (Plantilla local)
        if estatus == "ACEPTAR":
            return (f" Te recomendamos ACEPTAR el pedido #{pedido.get('pedido_id')}. "
                    f"Ofrece un pago de ${pago} MXN por {distancia} km, superando el umbral de rentabilidad "
                    f"incluso considerando el tráfico ({trafico}).")
        else:
            return (f" Te sugerimos RECHAZAR el pedido #{pedido.get('pedido_id')}. "
                    f"El pago de ${pago} MXN no compensa los {tiempo} min estimados de viaje bajo "
                    f"las condiciones actuales de tráfico ({trafico}).")

    def generar_reporte_turno(self, resumen_ia, resumen_baseline):
        """Genera una explicación ejecutiva comparando el desempeño del Agente IA vs Baseline."""
        prompt = f"""
Genera un resumen ejecutivo de 3 puntos sobre el desempeño del turno de entregas:

1. Agente IA Totales: ${resumen_ia.get('ganancias_totales_mxn')} MXN | {resumen_ia.get('km_totales')} km | {resumen_ia.get('tiempo_total_min')} min
2. Agente Baseline Totales: ${resumen_baseline.get('ganancias_totales_mxn')} MXN | {resumen_baseline.get('km_totales')} km | {resumen_baseline.get('tiempo_total_min')} min

Destaca el ahorro de tiempo, desgaste de vehículo y la eficiencia horaria del Agente IA.
"""
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                return response.text.strip()
            except Exception:
                pass

        # Fallback local
        ganancia_diff = round(resumen_ia.get('ganancias_totales_mxn', 0) - resumen_baseline.get('ganancias_totales_mxn', 0), 2)
        tiempo_diff = round(resumen_baseline.get('tiempo_total_min', 0) - resumen_ia.get('tiempo_total_min', 0), 1)
        
        return (
            f"📊 **Resumen Ejecutivo del Turno**\n"
            f"• **Mayor Eficiencia:** El Agente IA optimizó el tiempo trabajando {tiempo_diff} minutos menos.\n"
            f"• **Diferencia Financiera:** Variación neta de ${ganancia_diff} MXN comparado con aceptar todas las órdenes sin filtro.\n"
            f"• **Desgaste:** Se redujo el kilometraje ineficiente al rechazar ofertas de bajo valor."
        )