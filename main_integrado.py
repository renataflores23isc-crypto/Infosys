import json
import os
from pathlib import Path
from src.agente_rutas import AgenteBaseline, AgenteIA
from src.explicabilidad_llm import GeneradorExplicabilidad

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def cargar_pedidos(nombre_archivo):
    """Carga los archivos JSON generados por la Persona 2."""
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    print(f"⚠️ Archivo {nombre_archivo} no encontrado.")
    return []

def ejecutar_simulacion():
    print("==================================================================")
    print(" 🚀 SIMULADOR DE RUTAS E INTEGRACIÓN CON EXPLICABILIDAD LLM ")
    print("==================================================================\n")

    # 1. Cargar datasets (Persona 2)
    pedidos_estandar = cargar_pedidos(DATA_DIR / 'pedidos_monterrey.json')
    pedidos_pico = cargar_pedidos(DATA_DIR / 'evento_pico_demanda.json')
    
    # Combinar o seleccionar pedidos
    pedidos_totales = pedidos_estandar + pedidos_pico[:5]  # Ejemplo de mezcla de eventos

    # 2. Inicializar Agentes (Persona 3) y LLM (Persona 4)
    baseline = AgenteBaseline(costo_gasolina_km=2.5)
    agente_ia = AgenteIA(umbral_minimo_mxn_min=3.5, costo_gasolina_km=2.5)
    explicador = GeneradorExplicabilidad()

    # Factores ambientales (Persona 2)
    factor_trafico = 1.25  # Tráfico pesado
    factor_tarifa = 1.10   # Tarifa dinámica ligera

    print(f"📥 Procesando {len(pedidos_totales)} ofertas recibidas...\n")

    for i, pedido in enumerate(pedidos_totales, 1):
        res_b = baseline.procesar_oferta(pedido, factor_trafico, factor_tarifa)
        res_ia = agente_ia.procesar_oferta(pedido, factor_trafico, factor_tarifa)
        
        # Generar explicación en Lenguaje Natural (Persona 4)
        explicacion = explicador.generar_explicacion_decision(
            pedido, res_ia, clima="lluvia", trafico="pesado"
        )

        print(f"📦 Oferta #{pedido['pedido_id']} | Pago: ${pedido['pago_mxn']} MXN | Distancia: {pedido['distancia_km']} km")
        print(f" ├─ 🔴 Baseline: {res_b['decisión']} | Acumulado: ${res_b['ganancias_acumuladas']} MXN")
        print(f" ├─ 🟢 Agente IA: {res_ia['decisión']} | Acumulado: ${res_ia['ganancias_acumuladas']} MXN")
        print(f" └─ 💡 Explicación IA: {explicacion}\n")

    # 3. Resumen y Explicabilidad Final
    resumen_ia = agente_ia.obtener_resumen_estado()
    resumen_baseline = {
        "ganancias_totales_mxn": round(baseline.ganancias_acumuladas, 2),
        "km_totales": round(baseline.km_recorridos, 2),
        "tiempo_total_min": round(baseline.tiempo_acumulado_min, 1)
    }

    print("==================================================================")
    print(" 📈 REPORTE INTEGRADO Y EVALUACIÓN FINAL DE TURNO")
    print("==================================================================")
    
    reporte = explicador.generar_reporte_turno(resumen_ia, resumen_baseline)
    print(reporte)

if __name__ == "__main__":
    ejecutar_simulacion()