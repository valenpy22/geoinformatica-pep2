#!/usr/bin/env python
# coding: utf-8
"""
Módulo 05 – Síntesis final de resultados.

Esta sección:
- Carga métricas finales desde `final_metrics.csv`.
- Muestra mapas comparativos (real vs modelos), si existen.
- Muestra un gráfico de comparación de métricas finales.
- Presenta un breve texto de conclusiones generales.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "outputs" / "reports"


def run_section(st_module: st) -> None:
    """
    Ejecuta la sección 05 dentro de una aplicación Streamlit.

    Parameters
    ----------
    st_module : module
        Módulo `streamlit` inyectado desde la aplicación principal.
    """
    st_module.subheader("05. Síntesis final de resultados – Cerrillos")

    metrics_path = OUT_DIR / "final_metrics.csv"
    maps_path = OUT_DIR / "final_maps.png"
    metrics_plot_path = OUT_DIR / "final_metrics_plot.png"

    # -------------------------------------------------------------------------
    # 1. Métricas finales
    # -------------------------------------------------------------------------
    try:
        metrics = pd.read_csv(metrics_path)
        st_module.markdown("#### Métricas finales comparadas")
        st_module.dataframe(metrics, width="stretch")
    except Exception as exc:
        st_module.warning(
            "No se pudo cargar `final_metrics.csv`. "
            f"Detalle: {exc}"
        )

    # -------------------------------------------------------------------------
    # 2. Mapas comparativos (real vs modelos)
    # -------------------------------------------------------------------------
    st_module.markdown("#### Mapas comparativos: valores observados vs modelos")

    if maps_path.exists():
        st_module.image(str(maps_path), caption="Mapas comparativos (real vs modelos)")
    else:
        st_module.info("No se encontró `final_maps.png` en `outputs/reports`.")

    # -------------------------------------------------------------------------
    # 3. Gráfico de comparación de métricas
    # -------------------------------------------------------------------------
    st_module.markdown("#### Gráfico de comparación de métricas finales")

    if metrics_plot_path.exists():
        st_module.image(
            str(metrics_plot_path),
            caption="Comparación visual de métricas finales de los modelos",
        )
    else:
        st_module.info("No se encontró `final_metrics_plot.png` en `outputs/reports`.")

    # -------------------------------------------------------------------------
    # 4. Conclusiones generales
    # -------------------------------------------------------------------------
    st_module.markdown(
        """
        ### Conclusiones generales

        - Los modelos de Machine Learning capturan patrones espaciales relevantes en la comuna de Cerrillos.  
        - La geoestadística entrega información adicional sobre la variación espacial de las variables de interés.  
        - La combinación de ESDA, geoestadística y modelos de Machine Learning constituye una base cuantitativa 
          útil para apoyar decisiones de planificación y gestión territorial.
        """
    )
