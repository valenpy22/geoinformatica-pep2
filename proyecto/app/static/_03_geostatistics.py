#!/usr/bin/env python
# coding: utf-8
"""
Módulo 03 – Geoestadística.

Esta sección:
- Verifica la carga del límite comunal de Cerrillos (referencia espacial).
- Muestra el mapa interpolado obtenido por Kriging.
- Muestra el semivariograma experimental.
- Lee y presenta métricas de validación cruzada desde un archivo JSON, si existe.
"""

import json
from pathlib import Path

import geopandas as gpd
import streamlit as st

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
OUT_DIR = BASE_DIR / "outputs" / "reports"


def run_section(st_module: st) -> None:
    """
    Ejecuta la sección 03 dentro de una aplicación Streamlit.

    Parameters
    ----------
    st_module : module
        Módulo `streamlit` inyectado desde la aplicación principal.
    """
    st_module.subheader("03. Geoestadística – Cerrillos")

    # -------------------------------------------------------------------------
    # 1. Carga del límite comunal (solo referencia)
    # -------------------------------------------------------------------------
    try:
        _ = gpd.read_file(RAW_DIR / "cerrillos_limite.shp").to_crs(epsg=32719)
        st_module.success("Límite comunal cargado correctamente.")
    except Exception as exc:
        st_module.error(f"Error al cargar el límite comunal.\n\nDetalle: {exc}")
        return

    # -------------------------------------------------------------------------
    # 2. Mapa interpolado (Kriging)
    # -------------------------------------------------------------------------
    st_module.markdown("#### Mapa interpolado (Kriging)")

    krig_path = OUT_DIR / "geo_kriging_map.png"
    if krig_path.exists():
        st_module.image(str(krig_path), caption="Mapa interpolado mediante Kriging")
    else:
        st_module.warning(
            "No se encontró el archivo `geo_kriging_map.png` en `outputs/reports`."
        )

    # -------------------------------------------------------------------------
    # 3. Semivariograma experimental
    # -------------------------------------------------------------------------
    st_module.markdown("#### Semivariograma experimental")

    semiv_path = OUT_DIR / "geo_semivariograma.png"
    if semiv_path.exists():
        st_module.image(str(semiv_path), caption="Semivariograma experimental")
    else:
        st_module.warning(
            "No se encontró el archivo `geo_semivariograma.png` en `outputs/reports`."
        )

    # -------------------------------------------------------------------------
    # 4. Validación cruzada del modelo geoestadístico
    # -------------------------------------------------------------------------
    st_module.markdown("#### Validación cruzada del modelo")

    val_path = OUT_DIR / "geo_validation.json"
    if val_path.exists():
        try:
            with open(val_path, encoding="utf-8") as f:
                val = json.load(f)

            rmse = val.get("rmse", None)
            n_val = val.get("n_validados", None)

            if rmse is not None and n_val is not None:
                st_module.success(
                    f"Validación cruzada (20 % de los datos): "
                    f"RMSE = **{rmse:.2f} m²**, "
                    f"con **{n_val} puntos validados**."
                )
            else:
                st_module.info(
                    "El archivo `geo_validation.json` no contiene las claves "
                    "`rmse` y `n_validados` en el formato esperado."
                )
        except Exception as exc:
            st_module.error(
                "Ocurrió un error al leer `geo_validation.json`. "
                f"Detalle: {exc}"
            )
    else:
        st_module.info("No se encontró `geo_validation.json` en `outputs/reports`.")
