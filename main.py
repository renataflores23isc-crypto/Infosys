import streamlit as st
import pandas as pd
import json
import time

# -----------------------------------------------------------------------------
# 1. IMPORTAR AGENTES
# -----------------------------------------------------------------------------
try:
    from agente_rutas import AgenteBaseline, AgenteIA
except ImportError:
    st.error("❌ No se encontró el archivo 'agente_rutas.py'. Asegúrate de ejecutar Streamlit desde la carpeta del proyecto.")
    st.stop()

# -----------------------------------------------------------------------------
# 2. CONFIGURACIÓN DE PÁGINA STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Infosys - Optimización de Rutas IA",
    page_icon="🚴",
    layout="wide"
)

st.title("🚴 Infosys — Agente Inteligente de Optimización de Rutas")
st.caption("Hackathon Infosys | Monterrey, N.L. — Enrutamiento Dinámico con Explicabilidad IA")

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (PARÁMETROS)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Parámetros de Simulación")

escenario = st.sidebar.selectbox(
    "Escenario Dinámico:",
    ["Turno Normal", "Pico de Demanda / Imprevisto (Tráfico)"]
)

costo_gasolina = st.sidebar.number_input("Costo Gasolina ($/km):", value=2.5, step=0.5)
umbral_min = st.sidebar.number_input("Umbral IA Mínimo ($/min):", value=3.5, step=0.5)
velocidad = st.sidebar.slider("Velocidad de Simulación (seg/paso):", 0.3, 2.0, 0.8)

btn_ejecutar = st.sidebar.button("🚀 Iniciar Simulación en Vivo")

if "Pico" in escenario:
    factor_trafico_actual = 1.4
    factor_tarifa_actual = 1.2
    archivo_json = "evento_pico_demanda.json"
else:
    factor_trafico_actual = 1.0
    factor_tarifa_actual = 1.0
    archivo_json = "pedidos_monterrey.json"

# -----------------------------------------------------------------------------
# 4. TABLERO DE MÉTRICAS VISUALES
# -----------------------------------------------------------------------------
col_base, col_ia = st.columns(2)

with col_base:
    st.subheader("🔴 Modelo Baseline (FIFO)")
    st.caption("Acepta todos los pedidos en orden de llegada sin filtro.")
    m_base_g = st.empty()
    m_base_p = st.empty()
    m_base_km = st.empty()
    m_base_t = st.empty()
    
    m_base_g.metric("Ganancia Acumulada", "$0.00 MXN")
    m_base_p.metric("Pedidos Procesados", "0")
    m_base_km.metric("Distancia Recorrida", "0.0 km")
    m_base_t.metric("Tiempo Usado", "0 min")

with col_ia:
    st.subheader("🟢 Agente Inteligente IA (Infosys)")
    st.caption("Filtra por rentabilidad neta/min, tiempo y proximidad.")
    m_ia_g = st.empty()
    m_ia_p = st.empty()
    m_ia_km = st.empty()
    m_ia_t = st.empty()

    m_ia_g.metric("Ganancia Acumulada", "$0.00 MXN")
    m_ia_p.metric("Pedidos Procesados", "0")
    m_ia_km.metric("Distancia Recorrida", "0.0 km")
    m_ia_t.metric("Tiempo Usado", "0 min")

st.markdown("---")

col_mapa, col_llm = st.columns([1.2, 1.8])

with col_mapa:
    st.subheader("🗺️ Monitoreo de Rutas (MTY)")
    mapa_placeholder = st.empty()
    mapa_placeholder.map(pd.DataFrame({'lat': [25.6866], 'lon': [-100.3161]}), zoom=11)

with col_llm:
    st.subheader("🤖 Razonamiento Contextual LLM / IA")
    llm_box = st.container()
    with llm_box:
        st.info("Haz clic en **'🚀 Iniciar Simulación en Vivo'** para comenzar la evaluación.")

# -----------------------------------------------------------------------------
# 5. CICLO PRINCIPAL DE SIMULACIÓN (AMBOS CONTADORES FUNCIONALES)
# -----------------------------------------------------------------------------
if btn_ejecutar:
    try:
        with open(archivo_json, 'r', encoding='utf-8') as archivo:
            pedidos_disponibles = json.load(archivo)
    except FileNotFoundError:
        st.error(f"❌ No se encontró el archivo '{archivo_json}'.")
        st.stop()

    baseline = AgenteBaseline(costo_gasolina_km=costo_gasolina)
    agente_ia = AgenteIA(umbral_minimo_mxn_min=umbral_min, costo_gasolina_km=costo_gasolina)

    km_b_acumulados = 0.0
    puntos_ruta = [{'lat': 25.6866, 'lon': -100.3161}]

    for i, pedido in enumerate(pedidos_disponibles, 1):
        time.sleep(velocidad)

        res_b = baseline.procesar_oferta(pedido, factor_trafico_actual, factor_tarifa_actual)
        res_ia = agente_ia.procesar_oferta(pedido, factor_trafico_actual, factor_tarifa_actual)

        # ---------------------------------------------------------------------
        # ACTUALIZAR METRICAS BASELINE (CONTADOR 1)
        # ---------------------------------------------------------------------
        km_b_acumulados += float(pedido.get('distancia_km', 0.0))

        m_base_g.metric("Ganancia Acumulada", f"${round(baseline.ganancias_acumuladas, 2)} MXN")
        m_base_p.metric("Pedidos Procesados", f"{i}")  # Muestra 1, 2, 3... 10
        m_base_km.metric("Distancia Recorrida", f"{round(km_b_acumulados, 1)} km")
        m_base_t.metric("Tiempo Usado", f"{round(baseline.tiempo_acumulado_min, 1)} min")

        # ---------------------------------------------------------------------
        # ACTUALIZAR METRICAS AGENTE IA (CONTADOR 2 MULTI-DETECCIÓN)
        # ---------------------------------------------------------------------
        # 1. Extraer decisión de la IA sin importar si la llave es 'decisión' o 'decision'
        decision_ia_str = str(res_ia.get('decisión', res_ia.get('decision', ''))).lower()
        es_aceptado = "acept" in decision_ia_str

        # 2. Extraer conteo de pedidos aceptados por la IA de forma ultra-flexible
        conteo_ia_val = 0
        if hasattr(agente_ia, 'pedidos_aceptados'):
            attr_val = getattr(agente_ia, 'pedidos_aceptados')
            conteo_ia_val = len(attr_val) if isinstance(attr_val, list) else int(attr_val)
        elif 'pedidos_aceptados' in res_ia:
            res_val = res_ia['pedidos_aceptados']
            conteo_ia_val = len(res_val) if isinstance(res_val, list) else int(res_val)

        # 3. Extraer km del agente IA de forma ultra-flexible
        km_ia_val = res_ia.get('km_acumulados', getattr(agente_ia, 'km_acumulados', getattr(agente_ia, 'km_totales', 0.0)))

        m_ia_g.metric("Ganancia Acumulada", f"${round(agente_ia.ganancias_acumuladas, 2)} MXN")
        m_ia_p.metric("Pedidos Procesados", f"{conteo_ia_val}") # Muestra los aceptados reales (ej. 7)
        m_ia_km.metric("Distancia Recorrida", f"{round(float(km_ia_val), 1)} km")
        m_ia_t.metric("Tiempo Usado", f"{round(agente_ia.tiempo_acumulado_min, 1)} min")

        # ---------------------------------------------------------------------
        # DESPLIEGUE EXPLICATIVO Y MAPA
        # ---------------------------------------------------------------------
        razon_ia = res_ia.get('razón', res_ia.get('razon', 'Evaluado por algoritmo de rentabilidad.'))

        with llm_box:
            if es_aceptado:
                if 'origen' in pedido and 'destino' in pedido:
                    puntos_ruta.append({'lat': pedido['origen'][0], 'lon': pedido['origen'][1]})
                    puntos_ruta.append({'lat': pedido['destino'][0], 'lon': pedido['destino'][1]})
                    mapa_placeholder.map(pd.DataFrame(puntos_ruta), zoom=11)

                st.success(
                    f"**📦 Oferta #{pedido['pedido_id']} — ACEPTADA POR AGENTE IA**\n\n"
                    f"• **Pago:** ${pedido['pago_mxn']} MXN | **Distancia:** {pedido['distancia_km']} km | **Tiempo:** {pedido['tiempo_est_min']} min\n\n"
                    f"• **Justificación IA:** {razon_ia}"
                )
            else:
                st.warning(
                    f"**📦 Oferta #{pedido['pedido_id']} — RECHAZADA POR AGENTE IA**\n\n"
                    f"• **Pago:** ${pedido['pago_mxn']} MXN | **Distancia:** {pedido['distancia_km']} km | **Tiempo:** {pedido['tiempo_est_min']} min\n\n"
                    f"• **Justificación IA:** {razon_ia}"
                )

    # -------------------------------------------------------------------------
    # 6. RESUMEN FINAL
    # -------------------------------------------------------------------------
    horas_b = max(baseline.tiempo_acumulado_min / 60, 0.01)
    horas_ia = max(agente_ia.tiempo_acumulado_min / 60, 0.01)

    rate_b = round(baseline.ganancias_acumuladas / horas_b, 2)
    rate_ia = round(agente_ia.ganancias_acumuladas / horas_ia, 2)
    diff_rate = round(rate_ia - rate_b, 2)
    tiempo_ahorrado = round(baseline.tiempo_acumulado_min - agente_ia.tiempo_acumulado_min, 1)

    st.balloons()
    st.success(
        f"🏆 **Resumen Final del Turno:**\n\n"
        f"• **Baseline:** ${round(baseline.ganancias_acumuladas, 2)} MXN en {round(baseline.tiempo_acumulado_min, 1)} min ({rate_b} MXN/hr)\n\n"
        f"• **Agente IA:** ${round(agente_ia.ganancias_acumuladas, 2)} MXN en {round(agente_ia.tiempo_acumulado_min, 1)} min ({rate_ia} MXN/hr)\n\n"
        f"⚡ **Eficiencia:** La IA logró **+${diff_rate} MXN/hora** adicional trabajando **{tiempo_ahorrado} min menos**."
    )