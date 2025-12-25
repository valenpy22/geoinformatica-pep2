#!/usr/bin/env python
# coding: utf-8
"""
Módulo 04 – Resultados de modelos de Machine Learning.

Esta sección:
- Carga métricas de rendimiento de modelos desde `ml_metrics.csv`.
- Carga resultados espaciales (predicciones) desde `ml_results.geojson`.
- Muestra una tabla de métricas.
- Genera gráficos de barras comparando RMSE y R².
- Visualiza mapas de predicciones por modelo (Random Forest, XGBoost).
- Muestra figuras adicionales exportadas desde notebooks, si existen.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "outputs" / "reports"


def run_section(st_module: st) -> None:
    """
    Ejecuta la sección 04 dentro de una aplicación Streamlit.

    Parameters
    ----------
    st_module : module
        Módulo `streamlit` inyectado desde la aplicación principal.
    """
    st_module.subheader("04. Resultados de modelos de Machine Learning – Cerrillos")

    metrics_path = OUT_DIR / "ml_metrics.csv"
    results_geo_path = OUT_DIR / "ml_results.geojson"

    # -------------------------------------------------------------------------
    # 1. Carga de métricas y resultados espaciales
    # -------------------------------------------------------------------------
    try:
        metrics = pd.read_csv(metrics_path)
        buildings = gpd.read_file(results_geo_path)
    except Exception as exc:
        st_module.error(
            "No se pudieron cargar los resultados de Machine Learning desde `outputs/reports`.\n\n"
            f"Detalle: {exc}"
        )
        return

    if buildings.empty:
        st_module.warning(
            "El archivo `ml_results.geojson` está vacío. "
            "Verificar el proceso de guardado en el notebook 04."
        )
        return

    st_module.success("Resultados de modelos de Machine Learning cargados correctamente.")

    # -------------------------------------------------------------------------
    # 2. Tabla de métricas
    # -------------------------------------------------------------------------
    st_module.markdown("#### Métricas de los modelos")
    st_module.dataframe(metrics, width="stretch")

    # -------------------------------------------------------------------------
    # 3. Gráficos de barras: RMSE y R²
    # -------------------------------------------------------------------------
    st_module.markdown("#### Comparación de métricas (RMSE y R²)")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    sns.barplot(data=metrics, x="Modelo", y="RMSE", ax=ax[0])
    ax[0].set_title("RMSE por modelo")
    ax[0].tick_params(axis="x", rotation=45)

    sns.barplot(data=metrics, x="Modelo", y="R²", ax=ax[1])
    ax[1].set_title("R² por modelo")
    ax[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    st_module.pyplot(fig)

    # -------------------------------------------------------------------------
    # 4. Mapas de predicciones por modelo
    # -------------------------------------------------------------------------
    st_module.markdown("#### Mapas de predicciones por modelo")

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    # Random Forest
    if "pred_rf" in buildings.columns:
        buildings.plot(
            ax=axes[0],
            column="pred_rf",
            cmap="viridis",
            legend=True,
            legend_kwds={"shrink": 0.6},
        )
        axes[0].set_title("Predicción – Random Forest")
        axes[0].set_axis_off()
    else:
        axes[0].set_title("Random Forest")
        axes[0].text(0.5, 0.5, "Columna 'pred_rf' no encontrada", ha="center")
        axes[0].set_axis_off()

    # XGBoost
    if "pred_xgb" in buildings.columns:
        buildings.plot(
            ax=axes[1],
            column="pred_xgb",
            cmap="viridis",
            legend=True,
            legend_kwds={"shrink": 0.6},
        )
        axes[1].set_title("Predicción – XGBoost")
        axes[1].set_axis_off()
    else:
        axes[1].set_title("XGBoost")
        axes[1].text(0.5, 0.5, "Columna 'pred_xgb' no encontrada", ha="center")
        axes[1].set_axis_off()

    plt.tight_layout()
    st_module.pyplot(fig)

    # -------------------------------------------------------------------------
    # 5. Figuras adicionales exportadas
    # -------------------------------------------------------------------------
    st_module.markdown("#### Figuras adicionales exportadas")

    extra_imgs = [
        ("ml_comparacion.png", "Comparación visual de métricas de los modelos"),
        ("ml_mapas_predicciones.png", "Mapas de predicciones (resumen general)"),
    ]

    for fname, caption in extra_imgs:
        path = OUT_DIR / fname
        if path.exists():
            st_module.image(str(path), caption=caption)
        else:
            st_module.info(f"No se encontró la figura `{fname}` en `outputs/reports`.")
