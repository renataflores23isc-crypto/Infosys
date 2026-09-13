import math

class AgenteBaseline:
    """
    Agente Tradicional (Baseline / FIFO):
    Acepta todas las órdenes sin filtrar y entrega en el orden de llegada.
    """
    def __init__(self, costo_gasolina_km=2.5):
        self.costo_gasolina_km = costo_gasolina_km
        self.ganancias_acumuladas = 0.0
        self.km_recorridos = 0.0
        self.tiempo_acumulado_min = 0

    def procesar_oferta(self, pedido, factor_trafico=1.0, factor_tarifa=1.0):
        # Aplicar eventos dinámicos al pedido actual
        pago_ajustado = pedido["pago_mxn"] * factor_tarifa
        tiempo_ajustado = pedido["tiempo_est_min"] * factor_trafico

        costo_gasolina = pedido["distancia_km"] * self.costo_gasolina_km
        ganancia_neta = pago_ajustado - costo_gasolina

        # Acumular métricas del turno
        self.ganancias_acumuladas += ganancia_neta
        self.km_recorridos += pedido["distancia_km"]
        self.tiempo_acumulado_min += tiempo_ajustado

        return {
            "decisión": "ACEPTAR",
            "razón": "El agente baseline acepta todas las órdenes.",
            "ganancia_neta": round(ganancia_neta, 2),
            "ganancias_acumuladas": round(self.ganancias_acumuladas, 2),
            "km_acumulados": round(self.km_recorridos, 2),
            "tiempo_acumulado_min": round(self.tiempo_acumulado_min, 1)
        }


class AgenteIA:
    """
    Agente Inteligente (Optimizado para el repartidor):
    Filtra por rentabilidad neta por minuto, reacciona a eventos dinámicos
    y reorganiza la ruta de entregas según proximidad.
    """
    def __init__(self, umbral_minimo_mxn_min=3.0, costo_gasolina_km=2.5):
        self.umbral_minimo = umbral_minimo_mxn_min  # Mínimo $3 MXN por minuto
        self.costo_gasolina_km = costo_gasolina_km
        self.ganancias_acumuladas = 0.0
        self.km_recorridos = 0.0
        self.tiempo_acumulado_min = 0
        self.pedidos_aceptados = []

    def calcular_rentabilidad(self, pedido, factor_trafico=1.0, factor_tarifa=1.0):
        """Calcula Ganancia Neta / Minuto considerando imprevistos dinámicos."""
        pago_ajustado = pedido["pago_mxn"] * factor_tarifa
        tiempo_ajustado = pedido["tiempo_est_min"] * factor_trafico
        costo_combustible = pedido["distancia_km"] * self.costo_gasolina_km

        ganancia_neta = pago_ajustado - costo_combustible

        if tiempo_ajustado <= 0:
            return 0, ganancia_neta, tiempo_ajustado

        ratio_rentabilidad = ganancia_neta / tiempo_ajustado
        return ratio_rentabilidad, ganancia_neta, tiempo_ajustado

    def procesar_oferta(self, pedido, factor_trafico=1.0, factor_tarifa=1.0):
        ratio, ganancia_neta, tiempo_ajustado = self.calcular_rentabilidad(
            pedido, factor_trafico, factor_tarifa
        )

        # 1. Filtro Heurístico de Rentabilidad
        if ratio < self.umbral_minimo:
            return {
                "decisión": "RECHAZAR",
                "razón": f"Rentabilidad baja (${round(ratio, 2)} MXN/min vs umbral ${self.umbral_minimo} MXN/min).",
                "ganancia_neta": 0.0,
                "ganancias_acumuladas": round(self.ganancias_acumuladas, 2),
                "km_acumulados": round(self.km_recorridos, 2),
                "tiempo_acumulado_min": round(self.tiempo_acumulado_min, 1)
            }

        # 2. Aceptación del Pedido y Actualización
        self.pedidos_aceptados.append(pedido)
        self.ganancias_acumuladas += ganancia_neta
        self.km_recorridos += pedido["distancia_km"]
        self.tiempo_acumulado_min += tiempo_ajustado

        # 3. Optimización de la Secuencia de Entrega (Nearest Neighbor)
        ruta_optimizada = self.optimizar_secuencia_pedidos(self.pedidos_aceptados)

        return {
            "decisión": "ACEPTAR",
            "razón": f"Alta rentabilidad (${round(ratio, 2)} MXN/min). Pedido añadido a la ruta optimizada.",
            "ganancia_neta": round(ganancia_neta, 2),
            "ganancias_acumuladas": round(self.ganancias_acumuladas, 2),
            "km_acumulados": round(self.km_recorridos, 2),
            "tiempo_acumulado_min": round(self.tiempo_acumulado_min, 1),
            "secuencia_entrega_ids": [p["pedido_id"] for p in ruta_optimizada]
        }

    def optimizar_secuencia_pedidos(self, pedidos):
        """Ordena las entregas activas priorizando puntos más cercanos."""
        if not pedidos:
            return []

        no_visitados = list(pedidos)
        ruta = []
        punto_actual = no_visitados[0]["origen"]

        while no_visitados:
            siguiente_pedido = min(
                no_visitados,
                key=lambda p: self._distancia_haversine(punto_actual, p["origen"])
            )
            ruta.append(siguiente_pedido)
            punto_actual = siguiente_pedido["destino"]
            no_visitados.remove(siguiente_pedido)

        return ruta

    def obtener_resumen_estado(self):
        """Exporta el estado actual en dict/JSON para la Persona 4 (LLM / Explicabilidad)."""
        return {
            "ganancias_totales_mxn": round(self.ganancias_acumuladas, 2),
            "km_totales": round(self.km_recorridos, 2),
            "tiempo_total_min": round(self.tiempo_acumulado_min, 1),
            "pedidos_aceptados_count": len(self.pedidos_aceptados)
        }

    @staticmethod
    def _distancia_haversine(coord1, coord2):
        """Calcula distancia lineal entre dos coordenadas geográficas [lat, lon]."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        r = 6371.0  # Radio medio de la Tierra en km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c


# =====================================================================
# DEMOSTRACIÓN DE FUNCIONAMIENTO (Ejecuta este archivo directamente)
# =====================================================================
if __name__ == "__main__":
    pedidos_simulados = [
        {"pedido_id": 101, "origen": [25.6866, -100.3161], "destino": [25.6500, -100.2900], "pago_mxn": 95.0, "distancia_km": 4.5, "tiempo_est_min": 15},
        {"pedido_id": 102, "origen": [25.6700, -100.3100], "destino": [25.6400, -100.2800], "pago_mxn": 35.0, "distancia_km": 9.0, "tiempo_est_min": 40}, # Malo
        {"pedido_id": 103, "origen": [25.6600, -100.3000], "destino": [25.6300, -100.2700], "pago_mxn": 120.0, "distancia_km": 3.8, "tiempo_est_min": 18},
    ]

    baseline = AgenteBaseline()
    agente_ia = AgenteIA(umbral_minimo_mxn_min=3.5)

    print("=== SIMULACIÓN EN TIEMPO REAL ===\n")

    # Evento de prueba: Tráfico pesado moderado (+20% tiempo) y Tarifa dinámica (+10% pago)
    factor_trafico_actual = 1.2
    factor_tarifa_actual = 1.1

    for p in pedidos_simulados:
        res_b = baseline.procesar_oferta(p, factor_trafico_actual, factor_tarifa_actual)
        res_ia = agente_ia.procesar_oferta(p, factor_trafico_actual, factor_tarifa_actual)

        print(f"Pedido #{p['pedido_id']} | Oferta Base: ${p['pago_mxn']} MXN | Tiempo: {p['tiempo_est_min']} min")
        print(f" ├─ [Baseline]  Decisión: {res_b['decisión']} | Acumulado: ${res_b['ganancias_acumuladas']} MXN")
        print(f" └─ [Agente IA] Decisión: {res_ia['decisión']} | Razonamiento: {res_ia['razón']}")
        print(f"    └─ Acumulado IA: ${res_ia['ganancias_acumuladas']} MXN | Km: {res_ia['km_acumulados']} km\n")

    print("=== RESUMEN PARA PERSONA 4 (LLM) ===")
    print(agente_ia.obtener_resumen_estado())