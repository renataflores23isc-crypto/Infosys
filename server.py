import os
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.agente_rutas import AgenteBaseline, AgenteIA

try:
    from src.explicabilidad_llm import GeneradorExplicabilidad
    has_llm = True
except ImportError:
    has_llm = False

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return FileResponse(STATIC_DIR / "index.html")

def cargar_pedidos(nombre_archivo):
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.get("/api/simular")
def ejecutar_simulacion():
    pedidos_estandar = cargar_pedidos(DATA_DIR / 'pedidos_monterrey.json')
    pedidos_pico = cargar_pedidos(DATA_DIR / 'evento_pico_demanda.json')
    
    pedidos_totales = pedidos_estandar + pedidos_pico[:5]
    
    if not pedidos_totales:
        pedidos_totales = [
            {"pedido_id": "A-441", "origen": [25.6866, -100.3161], "destino": [25.6500, -100.2900], "pago_mxn": 95.0, "distancia_km": 4.5, "tiempo_est_min": 15},
            {"pedido_id": "B-112", "origen": [25.6700, -100.3100], "destino": [25.6400, -100.2800], "pago_mxn": 35.0, "distancia_km": 9.0, "tiempo_est_min": 40},
            {"pedido_id": "C-338", "origen": [25.6600, -100.3000], "destino": [25.6300, -100.2700], "pago_mxn": 120.0, "distancia_km": 3.8, "tiempo_est_min": 18},
            {"pedido_id": "D-891", "origen": [25.6800, -100.3200], "destino": [25.6550, -100.2950], "pago_mxn": 110.0, "distancia_km": 5.2, "tiempo_est_min": 20},
            {"pedido_id": "E-204", "origen": [25.6400, -100.2800], "destino": [25.6200, -100.2600], "pago_mxn": 40.0, "distancia_km": 6.5, "tiempo_est_min": 25}
        ]

    costo_gasolina = 2.5
    umbral_ia = 3.5
    factor_trafico = 1.25
    factor_tarifa = 1.10

    baseline = AgenteBaseline(costo_gasolina_km=costo_gasolina)
    agente_ia = AgenteIA(umbral_minimo_mxn_min=umbral_ia, costo_gasolina_km=costo_gasolina)

    pasos = []
    pedidos_aceptados_ia = []
    pedidos_rechazados_ia = []
    registro_eventos = []

    # Procesar paso a paso guardando snapshots de las métricas
    for idx, p in enumerate(pedidos_totales):
        res_b = baseline.procesar_oferta(p, factor_trafico, factor_tarifa)
        res_ia = agente_ia.procesar_oferta(p, factor_trafico, factor_tarifa)
        
        tiempo_ajustado = p["tiempo_est_min"] * factor_trafico
        costo_comb = p["distancia_km"] * costo_gasolina
        ganancia_neta = (p["pago_mxn"] * factor_tarifa) - costo_comb
        ratio = round(ganancia_neta / tiempo_ajustado, 2) if tiempo_ajustado > 0 else 0

        item_info = {"id": p["pedido_id"], "ratio": ratio}

        hora_actual = f"14:{10 + idx*5:02d}"

        if res_ia["decisión"] == "ACEPTAR":
            pedidos_aceptados_ia.append(item_info)
            registro_eventos.append({
                "hora": hora_actual,
                "evento": f"Pedido #{p['pedido_id']} recibido",
                "accion": f"Aceptado (${ratio}/min)",
                "clase": "action-accepted"
            })
        else:
            pedidos_rechazados_ia.append(item_info)
            registro_eventos.append({
                "hora": hora_actual,
                "evento": f"Pedido #{p['pedido_id']} evaluado",
                "accion": f"Rechazado (${ratio}/min < ${umbral_ia})",
                "clase": "action-reroute"
            })

        base_g = round(baseline.ganancias_acumuladas, 2)
        base_km = round(baseline.km_recorridos, 2)
        base_t = round(baseline.tiempo_acumulado_min, 1)
        base_h = round((base_g / (base_t / 60)), 2) if base_t > 0 else 0

        ia_g = round(agente_ia.ganancias_acumuladas, 2)
        ia_km = round(agente_ia.km_recorridos, 2)
        ia_t = round(agente_ia.tiempo_acumulado_min, 1)
        ia_r = round(ia_g / ia_t, 2) if ia_t > 0 else 0

        diff_g = round(((ia_g - base_g) / base_g * 100), 2) if base_g > 0 else 0
        diff_km = round(((base_km - ia_km) / base_km * 100), 2) if base_km > 0 else 0

        pasos.append({
            "paso_num": idx + 1,
            "pedido_id": p["pedido_id"],
            "baseline": {
                "ganancia": base_g,
                "ganancia_hora": base_h,
                "distancia": base_km,
                "pedidos": idx + 1
            },
            "agente_ia": {
                "ganancia": ia_g,
                "ratio": ia_r,
                "distancia": ia_km,
                "ahorro": max(diff_km, 0)
            },
            "mejora": {
                "ganancia_pct": f"+{diff_g}%",
                "distancia_pct": f"-{diff_km}%",
                "pct_num": min(max(diff_g, 0), 100)
            },
            "aceptados": list(pedidos_aceptados_ia),
            "rechazados": list(pedidos_rechazados_ia),
            "eventos": list(registro_eventos)
        })

    # Generar Explicación LLM
    explicacion_texto = ""
    if has_llm:
        try:
            explicador = GeneradorExplicabilidad()
            resumen_ia = agente_ia.obtener_resumen_estado()
            resumen_base = {
                "ganancias_totales_mxn": round(baseline.ganancias_acumuladas, 2),
                "km_totales": round(baseline.km_recorridos, 2),
                "tiempo_total_min": round(baseline.tiempo_acumulado_min, 1)
            }
            explicacion_texto = explicador.generar_reporte_turno(resumen_ia, resumen_base)
        except Exception:
            explicacion_texto = None

    if not explicacion_texto:
        rechazado_ej = pedidos_rechazados_ia[0] if pedidos_rechazados_ia else {"id": "B-112", "ratio": 1.8}
        aceptado_ej = pedidos_aceptados_ia[0] if pedidos_aceptados_ia else {"id": "C-338", "ratio": 4.1}
        explicacion_texto = f"El pedido #{rechazado_ej['id']} fue rechazado debido a que su ratio de ${rechazado_ej['ratio']}/min no superó el umbral mínimo de ${umbral_ia}/min bajo condiciones de tráfico pesado. Esto permitió priorizar pedidos de alto rendimiento como el #{aceptado_ej['id']} con ratio de ${aceptado_ej['ratio']}/min."

    return {
        "pasos": pasos,
        "explicacion_llm": explicacion_texto,
        "umbral_ia": umbral_ia
    }

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")