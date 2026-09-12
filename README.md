# 🚴 Infosys - Agente Inteligente de Optimización de Rutas y Entregas

Centro de trabajo y ensamblaje de proyecto asignado para Hackathon Infosys.

## 📌 Descripción del Proyecto
Sistema inteligente de toma de decisiones para repartidores de plataformas bajo demandas dinámicas, imprevistos viales y optimización de ganancias. Compara un modelo tradicional de atención sin filtro (Baseline FIFO) contra un **Agente IA** de optimización de rutas respaldado por explicabilidad contextual en tiempo real con **LLM**.

---

## 🏗️ Estructura del Proyecto y Roles

* **`entorno.py` (Persona 2 - Entorno y Datos):** Generación del grafo urbano de Monterrey (`OSMnx`), simulación de imprevistos dinámicos (clima/tráfico) y exportación de datsets JSON (`pedidos_monterrey.json`, `evento_pico_demanda.json`).
* **`agente_rutas.py` (Persona 3 - Algoritmos de IA):** Implementación de la heurística de rentabilidad neta por minuto (`AgenteIA`) y secuenciación de entregas por proximidad geodésica vs. la estrategia base (`AgenteBaseline`).
* **`explicabilidad_llm.py` (Persona 4 - Explicabilidad y LLM):** Módulo de lenguaje natural para traducción de decisiones algorítmicas y resúmenes ejecutivos usando modelos generativos Gemini.
* **`main_integrado.py` (Persona 4 - Integración y Pipeline):** Orquestador general que integra datos, ejecución de agentes y capa de explicabilidad.

---

## 🛠️ Requisitos e Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Infosys