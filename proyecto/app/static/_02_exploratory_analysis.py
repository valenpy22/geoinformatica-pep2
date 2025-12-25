#!/usr/bin/env python
# coding: utf-8
"""
Módulo 02 – Análisis exploratorio de datos espaciales (ESDA).

Esta sección:
- Carga el límite comunal y las edificaciones de Cerrillos.
- Calcula el área de cada edificio (en m²).
- Muestra un mapa simple de la distribución de edificios.
- Presenta un histograma de áreas.
- Muestra figuras ESDA previamente exportadas (si existen) desde `outputs/reports`.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
OUT_DIR = BASE_DIR / "outputs" / "reports"


def run_section(st_module: st) -> None:
    """
    Ejecuta la sección 02 dentro de una aplicación Streamlit.

    Parameters
    ----------
    st_module : module
        Módulo `streamlit` inyectado desde la aplicación principal.
    """
    st_module.subheader("02. Análisis exploratorio de datos espaciales (ESDA) – Cerrillos")

    # -------------------------------------------------------------------------
    # 1. Carga de datos espaciales
    # -------------------------------------------------------------------------
    try:
        cerrillos = gpd.read_file(RAW_DIR / "cerrillos_limite.shp").to_crs(epsg=32719)
        buildings = gpd.read_file(
            RAW_DIR / "osm_buildings_cerrillos.geojson"
        ).to_crs(epsg=32719)
    except Exception as exc:
        st_module.error(f"No se pudieron cargar los datos de Cerrillos.\n\nDetalle: {exc}")
        return

    # Cálculo de área de cada edificio
    buildings["area_m2"] = buildings.geometry.area
    st_module.success(
        f"Datos cargados correctamente. Se calcularon áreas para {len(buildings)} edificaciones."
    )

    # -------------------------------------------------------------------------
    # 2. Mapa base: distribución de edificios
    # -------------------------------------------------------------------------
    st_module.markdown("#### Mapa: distribución de edificaciones")

    fig, ax = plt.subplots(figsize=(8, 8))
    cerrillos.boundary.plot(ax=ax, color="red", linewidth=2)
    buildings.plot(
        ax=ax,
        color="lightgray",
        edgecolor="black",
        linewidth=0.2,
        alpha=0.7,
    )

    ax.set_title("Distribución de edificaciones en Cerrillos")
    ax.set_axis_off()

    # Leyenda manual
    legend_elements = [
        Line2D([0], [0], color="red", lw=2, label="Límite comunal"),
        Patch(facecolor="lightgray", edgecolor="black", label="Edificios"),
    ]
    ax.legend(handles=legend_elements, loc="lower left")

    st_module.pyplot(fig)

    # -------------------------------------------------------------------------
    # 3. Histograma de áreas de edificios
    # -------------------------------------------------------------------------
    st_module.markdown("#### Histograma de áreas de edificios")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(buildings["area_m2"], kde=True, ax=ax, bins=50)
    ax.set_xlabel("Área (m²)")
    ax.set_ylabel("Frecuencia")
    ax.set_title("Distribución de área de edificaciones")
    st_module.pyplot(fig)

    # -------------------------------------------------------------------------
    # 4. Mapas ESDA exportados desde notebooks
    # -------------------------------------------------------------------------
    st_module.markdown("#### Mapas ESDA exportados")

    esda_imgs = [
        ("esda_mapa_base.png", "Mapa base de Cerrillos"),
        ("esda_area_tematica.png", "Mapa temático por área de edificios"),
        ("esda_clusters_lisa.png", "Clusters LISA"),
        ("esda_hotspots.png", "Mapa de hotspots"),
        ("esda_semivariograma.png", "Semivariograma (ESDA)"),
    ]

    for fname, caption in esda_imgs:
        path = OUT_DIR / fname
        if path.exists():
            st_module.image(str(path), caption=caption)
        else:
            st_module.info(f"No se encontró la figura `{fname}` en `outputs/reports`.")
