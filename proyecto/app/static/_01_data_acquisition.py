#!/usr/bin/env python
# coding: utf-8
"""
Módulo 01 – Adquisición y exploración básica de datos espaciales.

Esta sección:
- Lista los archivos disponibles en el directorio `data/raw`.
- Carga el límite comunal de Cerrillos y las edificaciones desde OSM.
- Genera una visualización simple del límite comunal y los edificios.

Se asume que:
- El script se ejecuta dentro de una estructura de proyecto donde `BASE_DIR`
  es dos niveles por encima de la carpeta que contiene este archivo.
- Existen los archivos:
    - data/raw/cerrillos_limite.shp
    - data/raw/osm_buildings_cerrillos.geojson
"""

from pathlib import Path
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"


def run_section(st_module: st) -> None:
    """
    Ejecuta la sección 01 dentro de una aplicación Streamlit.

    Parameters
    ----------
    st_module : module
        Módulo `streamlit` inyectado desde la aplicación principal. Se utiliza
        para escribir texto, mostrar figuras y manejar mensajes de error.
    """
    comuna = "Cerrillos"

    st_module.subheader("01. Adquisición y exploración básica de datos")
    st_module.write(f"Comuna seleccionada: **{comuna}**")

    # -------------------------------------------------------------------------
    # 1. Listar archivos disponibles en data/raw
    # -------------------------------------------------------------------------
    try:
        archivos = os.listdir(RAW_DIR)
        st_module.markdown("#### Archivos disponibles en `data/raw`")
        st_module.write(archivos)
    except Exception as exc:
        st_module.error(f"No se pudo listar el contenido de `{RAW_DIR}`.\n\nDetalle: {exc}")
        return

    # Opcional: estilo básico de Matplotlib (sin temas recargados)
    plt.style.use("default")

    # -------------------------------------------------------------------------
    # 2. Carga de datos espaciales
    # -------------------------------------------------------------------------
    try:
        limite = gpd.read_file(RAW_DIR / "cerrillos_limite.shp").to_crs(epsg=32719)
        buildings = gpd.read_file(
            RAW_DIR / "osm_buildings_cerrillos.geojson"
        ).to_crs(epsg=32719)
    except Exception as exc:
        st_module.error(f"No se pudieron cargar los datos espaciales requeridos.\n\nDetalle: {exc}")
        return

    st_module.success(f"Datos cargados correctamente. Total de edificaciones: {len(buildings)}.")

    # -------------------------------------------------------------------------
    # 3. Visualización: límite comunal + edificaciones
    # -------------------------------------------------------------------------
    st_module.subheader("Límite comunal y edificaciones OSM")

    fig, ax = plt.subplots(figsize=(10, 10))
    limite.boundary.plot(ax=ax, color="red", linewidth=2, label="Límite comunal")
    buildings.plot(
        ax=ax,
        color="lightgray",
        edgecolor="black",
        linewidth=0.2,
        alpha=0.7,
    )
    ax.set_title(f"{comuna} – Límite comunal y edificaciones (OSM)")
    ax.set_axis_off()

    st_module.pyplot(fig)
