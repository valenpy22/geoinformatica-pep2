#!/usr/bin/env python
# coding: utf-8
"""
Aplicación web para visualización del análisis geoespacial de Cerrillos.

Autores:
- Diego Valdés
- Valentina Campos

La aplicación está construida con Streamlit y organiza el análisis en cinco módulos:
01. Adquisición de datos
02. Análisis exploratorio
03. Geoestadística
04. Modelos de Machine Learning
05. Síntesis de resultados

La comuna puede configurarse mediante la variable de entorno `COMUNA_NAME`.
"""

import os
from pathlib import Path

import folium
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

# Importar secciones
from _01_data_acquisition import run_section as sec_data_acq
from _02_exploratory_analysis import run_section as sec_esda
from _03_geostatistics import run_section as sec_geo
from _04_machine_learning import run_section as sec_ml
from _05_results_synthesis import run_section as sec_summary

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv()

COMUNA = os.getenv("COMUNA_NAME") or "Cerrillos"

st.set_page_config(
    page_title=f"Análisis territorial – {COMUNA}",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("Sistema de análisis territorial")
st.markdown(f"### Comuna analizada: **{COMUNA}**")

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Navegación")

    page = st.selectbox(
        "Seleccione una sección:",
        [
            "Inicio",
            "01. Adquisición de datos",
            "02. Análisis exploratorio",
            "03. Geoestadística",
            "04. Modelos de Machine Learning",
            "05. Síntesis de resultados",
        ],
    )

    st.markdown("---")
    st.info(
        """
        Laboratorio Integrador – Geoinformática 2025

        Proyecto comunal: Cerrillos  
        Desarrollado por:  
        - Diego Valdés  
        - Valentina Campos
        """
    )

# ---------------------------------------------------------------------------
# Contenido según la página seleccionada
# ---------------------------------------------------------------------------

if page == "Inicio":
    st.subheader("Resumen general del proyecto")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Ubicación aproximada de la comuna")

        # Mapa simple centrado en la comuna (coordenadas aproximadas)
        map_center = [-33.49, -70.71]
        m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")
        folium.Marker(
            map_center,
            popup=COMUNA,
            tooltip=COMUNA,
        ).add_to(m)

        st_folium(m, height=400, width=None)

    with col2:
        st.markdown("#### Objetivos del análisis")
        st.markdown(
            """
            - Integrar distintas fuentes de datos espaciales para la comuna de estudio.  
            - Analizar la distribución de edificaciones y variables territoriales relevantes.  
            - Aplicar técnicas de geoestadística y modelos de Machine Learning.  
            - Generar una síntesis visual y cuantitativa que apoye la toma de decisiones territoriales.
            """
        )

elif page == "01. Adquisición de datos":
    sec_data_acq(st)

elif page == "02. Análisis exploratorio":
    sec_esda(st)

elif page == "03. Geoestadística":
    sec_geo(st)

elif page == "04. Modelos de Machine Learning":
    sec_ml(st)

elif page == "05. Síntesis de resultados":
    sec_summary(st)

# ---------------------------------------------------------------------------
# Pie de página
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <p>Laboratorio Integrador – Geoinformática 2025</p>
        <p>Proyecto desarrollado por <strong>Diego Valdés</strong> y <strong>Valentina Campos</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)
