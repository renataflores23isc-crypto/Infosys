import json
import time
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA (TEMA OSCURO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Infosys Route Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS personalizados para interfaz oscura y limpia
st.markdown(
    """
    <style>
    /* Estilo Global Dark Mode */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Contenedores y Tarjetas */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card-ai {
        background-color: #1E293B;
        border: 1px solid #10B981;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }
    
    /* Tipografía y Textos */
    .card-title {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-value {
        color: #F8FAFC;
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .card-value-ai {
        color: #10B981;
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    
    /* Badges */
    .badge-baseline {
        background-color: #334155;
        color: #94A3B8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-ai {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-alert {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
    }
    
    /* Ocultar barra superior por defecto de Streamlit */
    header {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. IMPORTACIÓN DE MÓDULOS DEL PROYECTO (FALLBACK MOCK SI NO EXISTEN)
# -----------------------------------------------------------------------------
try:
    from agente_rutas import AgenteBaseline, AgenteIA
    from explicabilidad_llm import generar_explicacion
except ImportError:

    # Mock clases si se prueba el UI de manera independiente
    class AgenteBaseline:

        def ejecutar(self):
            return {
                "ganancia": 320.0,
                "ganancia_hora": 106.6,
                "distancia": 24.5,
                "completados": 4,
                "rechazados": 0,
            }

    class AgenteIA:

        def ejecutar(self):
            return {
                "ganancia": 580.0,
                "ratio_min": 4.8,
                "distancia": 18.2,
                "completados": 6,
                "ahorro_gas": 35.0,
            }

    def generar_explicacion(evento):
        return "El Agente IA rechazó la Orden #102 por bajo retorno ($1.8/min) y priorizó un clúster de alta demanda en San Pedro, maximizando el margen de ganancia."


# -----------------------------------------------------------------------------
# 3. ENCABEZADO Y CONTROLES
# -----------------------------------------------------------------------------
col_header, col_status, col_controls = st.columns([2, 1.5, 1.5])

with col_header:
    st.markdown("### ⚡ Infosys Route Optimizer")
    st.caption("Hackathon Challenge | Agente IA vs Baseline FIFO")

with col_status:
    st.markdown(
        """
        <div style="text-align: right; margin-top: 10px;">
            <span class="badge-alert">📍 Monterrey, NL</span>
            <span class="badge-alert">🌧️ Lluvia / Trafico Alto</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_controls:
    btn_simular = st.button(
        "▶ Iniciar Simulación", type="primary", use_container_width=True
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. MAPAS INTERACTIVOS (MONTERREY)
# -----------------------------------------------------------------------------
m_baseline = folium.Map(
    location=[25.6866, -100.3161], zoom_start=12, tiles="CartoDB dark_matter"
)
m_ai = folium.Map(
    location=[25.6866, -100.3161], zoom_start=12, tiles="CartoDB dark_matter"
)

# Ejemplo de Marcadores y Rutas Baseline
folium.Marker(
    [25.6866, -100.3161],
    popup="Origen FIFO",
    icon=folium.Icon(color="gray", icon="info-sign"),
).add_to(m_baseline)
folium.PolyLine(
    [[25.6866, -100.3161], [25.6500, -100.2900]], color="#64748B", weight=3
).add_to(m_baseline)

# Ejemplo de Marcadores y Rutas Agente IA
folium.Marker(
    [25.6866, -100.3161],
    popup="Origen Optimizado",
    icon=folium.Icon(color="green", icon="ok-sign"),
).add_to(m_ai)
folium.PolyLine(
    [[25.6866, -100.3161], [25.6600, -100.3300]], color="#10B981", weight=4
).add_to(m_ai)

# -----------------------------------------------------------------------------
# 5. DASHBOARD COMPARATIVO LADO A LADO
# -----------------------------------------------------------------------------
col_left, col_right = st.columns(2)

# --- COLUMNA IZQUIERDA: BASELINE ---
with col_left:
    st.markdown(
        '<div><span class="badge-baseline">ESTRATEGIA BASELINE (FIFO)</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### ")

    # Métricas 2x2
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="card-title">Ganancia Total</div>
                <div class="card-value">$320.00 MXN</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="metric-card">
                <div class="card-title">Distancia Recorrida</div>
                <div class="card-value">24.5 km</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="card-title">Ganancia / Hora</div>
                <div class="card-value">$106.60 /h</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="metric-card">
                <div class="card-title">Entregas Completadas</div>
                <div class="card-value">4 Pedidos</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st_folium(m_baseline, height=320, width=None, key="map_baseline")

# --- COLUMNA DERECHA: AGENTE IA ---
with col_right:
    st.markdown(
        '<div><span class="badge-ai">⚡ AGENTE IA INFOSYS</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### ")

    # Métricas 2x2
    m3, m4 = st.columns(2)
    with m3:
        st.markdown(
            """
            <div class="metric-card-ai">
                <div class="card-title">Ganancia Neta</div>
                <div class="card-value-ai">$580.00 MXN</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="metric-card-ai">
                <div class="card-title">Distancia Recorrida</div>
                <div class="card-value-ai">18.2 km</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            """
            <div class="metric-card-ai">
                <div class="card-title">Ratio de Rentabilidad</div>
                <div class="card-value-ai">$4.80 /min</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="metric-card-ai">
                <div class="card-title">Ahorro Estimado</div>
                <div class="card-value-ai">35% Combustible</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st_folium(m_ai, height=320, width=None, key="map_ai")

# -----------------------------------------------------------------------------
# 6. PANEL INFERIOR: EXPLICABILIDAD LLM Y EVENTOS
# -----------------------------------------------------------------------------
st.markdown("---")
col_llm, col_log = st.columns([1.8, 1.2])

with col_llm:
    st.markdown("#### 🤖 Explicabilidad Contextual en Tiempo Real (LLM)")
    explicacion_texto = generar_explicacion("evento_lluvia_pico")
    st.info(f"**Análisis de Decisión:**\n\n{explicacion_texto}")

with col_log:
    st.markdown("#### 📋 Registro de Eventos Dinámicos")
    eventos_df = pd.DataFrame(
        [
            {
                "Hora": "18:05",
                "Evento": "Pedido #104 Ofrecido",
                "Acción IA": "Aceptado ($4.8/min)",
            },
            {
                "Hora": "18:08",
                "Evento": "Lluvia en Av. Constitución",
                "Acción IA": "Reenrutamiento Óptimo",
            },
            {
                "Hora": "18:12",
                "Evento": "Pedido #105 Ofrecido",
                "Acción IA": "Rechazado (Bajo Margen)",
            },
        ]
    )
    st.dataframe(eventos_df, hide_index=True, use_container_width=True)