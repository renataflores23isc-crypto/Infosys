import json
import streamlit as st
import folium

# Importar la lógica desarrollada por el equipo
from agente_rutas import AgenteBaseline, AgenteIA
import explicabilidad_llm

# 1. Configuración de página
st.set_page_config(
    page_title="El Repartidor — Agente IA para Conductores",
    page_icon="🚚",
    layout="wide"
)

# 2. CSS Limpio (Sin zoom global que rompa el layout)
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    .stApp {
        background-color: #0a0d11;
        color: #ffffff;
    }

    h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Botón verde neón */
    div.stButton > button:first-child {
        background-color: #00e676 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 0 15px rgba(0, 230, 118, 0.4) !important;
        padding: 14px 20px !important;
    }

    div.stButton > button:first-child:hover {
        background-color: #00c853 !important;
        color: #ffffff !important;
    }

    /* Ocultar elementos sobrantes de Streamlit */
    header[data-testid="stHeader"] { background: rgba(0,0,0,0); }
    div[data-testid="stToolbar"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. Cargar datos
@st.cache_data
def cargar_datos():
    try:
        with open("pedidos_monterrey.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("No se encontró 'pedidos_monterrey.json'.")
        return []

pedidos_disponibles = cargar_datos()

# 4. Estado de la sesión
if "baseline" not in st.session_state:
    st.session_state.baseline = AgenteBaseline(costo_gasolina_km=2.5)
    st.session_state.agente_ia = AgenteIA(umbral_minimo_mxn_min=3.5, costo_gasolina_km=2.5)
    st.session_state.historial = []
    st.session_state.indice_pedido = 0

# 5. HEADER
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("## 🚚 **El Repartidor — Agente IA para Conductores**")
with col_head2:
    st.markdown("""
        <div style="text-align: right; padding-top: 5px;">
            <span style="background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid rgba(0, 230, 118, 0.3); padding: 6px 14px; border-radius: 15px; font-size: 13px; font-weight: 600;">● Turno en Vivo Monterrey</span>
            <span style="background: rgba(255, 255, 255, 0.05); color: #8e9aab; border: 1px solid #212b36; padding: 6px 14px; border-radius: 15px; font-size: 13px; margin-left: 8px;">Infosys Track 3</span>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# 6. LAYOUT PRINCIPAL
col_sidebar, col_main = st.columns([1.1, 3.9])

# BARRA LATERAL
with col_sidebar:
    st.markdown("### ⚡ Eventos del Turno en Vivo")
    st.caption("Modifica las condiciones climáticas y del mercado en tiempo real para evaluar al Agente IA.")
    
    factor_trafico = st.slider("Tráfico / Lluvia", 1.0, 2.0, 1.0, step=0.1)
    factor_tarifa = st.slider("Tarifa Dinámica", 1.0, 2.0, 1.0, step=0.1)

    st.write("")
    
    if st.button("► Procesar Siguiente Pedido", use_container_width=True):
        if st.session_state.indice_pedido < len(pedidos_disponibles):
            p_actual = pedidos_disponibles[st.session_state.indice_pedido]
            
            res_b = st.session_state.baseline.procesar_oferta(p_actual, factor_trafico, factor_tarifa)
            res_ia = st.session_state.agente_ia.procesar_oferta(p_actual, factor_trafico, factor_tarifa)
            
            if hasattr(explicabilidad_llm, 'generar_explicacion_llm'):
                explicacion = explicabilidad_llm.generar_explicacion_llm(p_actual, res_ia)
            elif hasattr(explicabilidad_llm, 'generar_explicacion'):
                explicacion = explicabilidad_llm.generar_explicacion(p_actual, res_ia)
            elif hasattr(explicabilidad_llm, 'explicar_decision'):
                explicacion = explicabilidad_llm.explicar_decision(p_actual, res_ia)
            else:
                explicacion = res_ia.get("razón", "Decisión procesada según métricas de rentabilidad.")
            
            st.session_state.historial.append({
                "pedido": p_actual,
                "baseline": res_b,
                "ia": res_ia,
                "explicacion": explicacion
            })
            st.session_state.indice_pedido += 1

    if st.button("🔄 Reiniciar Turno", use_container_width=True):
        st.session_state.baseline = AgenteBaseline(costo_gasolina_km=2.5)
        st.session_state.agente_ia = AgenteIA(umbral_minimo_mxn_min=3.5, costo_gasolina_km=2.5)
        st.session_state.historial = []
        st.session_state.indice_pedido = 0
        st.rerun()

    st.markdown("""
        <div style="margin-top: 35px; border-top: 1px solid #212b36; padding-top: 15px;">
            <span style="font-size: 11px; font-weight: 700; color: #5c6979; letter-spacing: 0.5px;">DIRECTIVA DEL SISTEMA</span>
            <p style="font-size: 12px; color: #8e9aab; margin-top: 6px; line-height: 1.4;">
                Maximizar el ingreso neto reduciendo tiempos de espera y trayectos sin carga en el área metropolitana de Monterrey.
            </p>
        </div>
    """, unsafe_allow_html=True)

# PANEL DERECHO
with col_main:
    
    hrs_b = max(st.session_state.baseline.tiempo_acumulado_min / 60, 0.01)
    hrs_ia = max(st.session_state.agente_ia.tiempo_acumulado_min / 60, 0.01)

    rate_b = round(st.session_state.baseline.ganancias_acumuladas / hrs_b, 2) if st.session_state.baseline.tiempo_acumulado_min > 0 else 0.0
    rate_ia = round(st.session_state.agente_ia.ganancias_acumuladas / hrs_ia, 2) if st.session_state.agente_ia.tiempo_acumulado_min > 0 else 0.0
    diff_rate = round(rate_ia - rate_b, 2)

    col_kpi1, col_kpi2 = st.columns(2)
    
    with col_kpi1:
        st.markdown(f"""
            <div style="background: #11161d; border: 1px solid #212b36; border-radius: 12px; padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 16px; font-weight: 700; color: #ffffff;">Agente Baseline</span>
                    <span style="font-size: 12px; color: #8e9aab;">Estrategia Golosa</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #8e9aab; font-size: 14px;">Ganancia Horaria</span>
                    <span style="font-weight: 600; color: #ffffff;">${rate_b} MXN/hr</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #8e9aab; font-size: 14px;">Total Ganado</span>
                    <span style="font-weight: 600; color: #ffffff;">${round(st.session_state.baseline.ganancias_acumuladas, 2)} MXN</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8e9aab; font-size: 14px;">Tiempo Activo</span>
                    <span style="font-weight: 600; color: #ffffff;">{round(st.session_state.baseline.tiempo_acumulado_min, 1)} min</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
            <div style="background: #131c23; border: 1px solid #00a854; border-radius: 12px; padding: 18px; box-shadow: 0 0 16px rgba(0, 230, 118, 0.12);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 16px; font-weight: 700; color: #ffffff;">Agente IA</span>
                        <span style="background: rgba(0, 230, 118, 0.15); color: #00e676; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 8px;">RECOMENDADO</span>
                    </div>
                    <span style="background: rgba(0, 230, 118, 0.15); color: #00e676; font-size: 13px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">+${diff_rate} MXN/hr vs Baseline</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #8e9aab; font-size: 14px;">Ganancia Horaria</span>
                    <span style="font-weight: 700; color: #00e676; font-size: 17px;">${rate_ia} MXN/hr</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #8e9aab; font-size: 14px;">Total Ganado</span>
                    <span style="font-weight: 600; color: #ffffff;">${round(st.session_state.agente_ia.ganancias_acumuladas, 2)} MXN</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8e9aab; font-size: 14px;">Tiempo Activo</span>
                    <span style="font-weight: 600; color: #ffffff;">{round(st.session_state.agente_ia.tiempo_acumulado_min, 1)} min</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    col_mapa, col_llm = st.columns([1.4, 1])

    with col_mapa:
        st.markdown("#### 🗺️ Mapa de Ruta en Vivo — Monterrey")
        
        # OpenStreetMap 100% libre sin API Key
        m = folium.Map(
            location=[25.6700, -100.3150], 
            zoom_start=13, 
            tiles="OpenStreetMap"
        )
        
        for item in st.session_state.historial:
            p = item["pedido"]
            dec_ia = item["ia"]["decisión"]
            color_p = "green" if dec_ia == "ACEPTAR" else "red"
            
            folium.Marker(
                location=p["origen"],
                popup=f"Pick #{p['pedido_id']} - ${p['pago_mxn']} MXN",
                icon=folium.Icon(color=color_p, icon="play")
            ).add_to(m)
            
            folium.Marker(
                location=p["destino"],
                popup=f"Drop #{p['pedido_id']}",
                icon=folium.Icon(color="blue", icon="stop")
            ).add_to(m)
            
            folium.PolyLine(
                locations=[p["origen"], p["destino"]],
                color="#00e676" if dec_ia == "ACEPTAR" else "#ff3366",
                weight=3,
                opacity=0.8,
                dash_array="5, 10"
            ).add_to(m)

        st.components.v1.html(m._repr_html_(), height=420)

    with col_llm:
        st.markdown("#### 🤖 Razonamiento del LLM")
        
        if not st.session_state.historial:
            st.markdown("<p style='color: #8e9aab; font-style: italic;'>Presiona <b>► Procesar Siguiente Pedido</b> para observar el razonamiento dinámico.</p>", unsafe_allow_html=True)
        else:
            for item in reversed(st.session_state.historial):
                p = item["pedido"]
                ia = item["ia"]
                exp = item["explicacion"]
                
                es_aceptado = ia["decisión"] == "ACEPTAR"
                border_color = "#00e676" if es_aceptado else "#ff3366"
                badge_bg = "rgba(0, 230, 118, 0.15)" if es_aceptado else "rgba(255, 51, 102, 0.15)"
                badge_color = "#00e676" if es_aceptado else "#ff3366"
                estado_lbl = "ACEPTADO" if es_aceptado else "RECHAZADO"
                dot_color = "🟢" if es_aceptado else "🔴"
                
                card_html = f"""
                <div style="
                    border-left: 4px solid {border_color};
                    background-color: #161c24;
                    padding: 14px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-top: 1px solid #212b36;
                    border-right: 1px solid #212b36;
                    border-bottom: 1px solid #212b36;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 14px; color: #ffffff;">{dot_color} Pedido #{p['pedido_id']}</span>
                        <span style="background: {badge_bg}; color: {badge_color}; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">{estado_lbl}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;">
                        <span style="color: #8e9aab;">Monto del Servicio</span>
                        <span style="font-weight: 700; color: {border_color};">${p['pago_mxn']} MXN</span>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 9px; border-radius: 6px; font-size: 13px; color: #d1d5db; font-style: italic;">
                        "{exp}"
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)