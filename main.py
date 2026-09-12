import json
from agente_rutas import AgenteBaseline, AgenteIA

# 1. Cargar el dataset de pedidos generado por la Persona 2
with open('pedidos_monterrey.json', 'r', encoding='utf-8') as archivo:
    pedidos_disponibles = json.load(archivo)

# 2. Inicializar tus agentes
baseline = AgenteBaseline(costo_gasolina_km=2.5)
agente_ia = AgenteIA(umbral_minimo_mxn_min=3.5, costo_gasolina_km=2.5)

print("==================================================")
print("  INICIANDO TURNO SIMULADO EN MONTERREY (TRACK 3) ")
print("==================================================\n")

# Factores de imprevistos dinámicos (puedes cambiarlos según los eventos de la Persona 2)
factor_trafico_actual = 1.0
factor_tarifa_actual = 1.0

# 3. Procesar la lista de pedidos en ambos agentes
for pedido in pedidos_disponibles:
    res_b = baseline.procesar_oferta(pedido, factor_trafico_actual, factor_tarifa_actual)
    res_ia = agente_ia.procesar_oferta(pedido, factor_trafico_actual, factor_tarifa_actual)

    print(f"📦 Oferta #{pedido['pedido_id']} | Pago: ${pedido['pago_mxn']} MXN | Distancia: {pedido['distancia_km']} km | Tiempo: {pedido['tiempo_est_min']} min")
    print(f" ├─ [Baseline]  Decisión: {res_b['decisión']} | Ganancia Acumulada: ${res_b['ganancias_acumuladas']} MXN")
    print(f" └─ [Agente IA] Decisión: {res_ia['decisión']} ({res_ia['razón']})")
    print(f"    └─ Ganancia IA Acumulada: ${res_ia['ganancias_acumuladas']} MXN | Km Totales: {res_ia['km_acumulados']} km\n")

print("==================================================")
print("              RESUMEN FINAL DEL TURNO             ")
print("==================================================")

# Convertir minutos a horas para calcular tasa horaria
horas_b = baseline.tiempo_acumulado_min / 60 if baseline.tiempo_acumulado_min > 0 else 1
horas_ia = agente_ia.tiempo_acumulado_min / 60 if agente_ia.tiempo_acumulado_min > 0 else 1

rate_b = round(baseline.ganancias_acumuladas / horas_b, 2)
rate_ia = round(agente_ia.ganancias_acumuladas / horas_ia, 2)

print(f"🔴 Baseline Total:  ${round(baseline.ganancias_acumuladas, 2)} MXN en {round(baseline.tiempo_acumulado_min, 1)} min ({rate_b} MXN/hora)")
print(f"🟢 Agente IA Total: ${round(agente_ia.ganancias_acumuladas, 2)} MXN en {round(agente_ia.tiempo_acumulado_min, 1)} min ({rate_ia} MXN/hora)")
print(f"⚡ Eficiencia Horaria: La IA ganó +${round(rate_ia - rate_b, 2)} MXN por hora trabajando {round(baseline.tiempo_acumulado_min - agente_ia.tiempo_acumulado_min, 1)} min menos.")