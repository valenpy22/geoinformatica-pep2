"""
==============================================================================
MÓDULO DE CONFIGURACIÓN - PROYECTO DESIERTOS DE SERVICIOS (PEP 1)
==============================================================================
Este script centraliza:
1. Rutas absolutas del proyecto (para que funcione en cualquier PC).
2. Configuración de estilos gráficos (Matplotlib/Seaborn).
3. Funciones auxiliares de carga y guardado de datos.

Uso: %run ./00_template.py
"""

import sys
import warnings
from pathlib import Path
from typing import Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# ============================================================================
# 0. CONFIGURACIÓN GLOBAL
# ============================================================================

# Ignorar advertencias no críticas (limpia la salida de los notebooks)
warnings.filterwarnings('ignore')

# Configuración visual por defecto
plt.style.use("seaborn-v0_8-whitegrid") # O "ggplot", "default"
sns.set_context("notebook", font_scale=1.1)

# ============================================================================
# 1. GESTIÓN DE RUTAS (PATH MANAGEMENT)
# ============================================================================

# Detectar ubicación actual
try:
    NOTEBOOKS_DIR = Path(__file__).resolve().parent
except NameError:
    # Fallback por si se ejecuta interactivamente sin archivo físico
    NOTEBOOKS_DIR = Path.cwd()

BASE_DIR = NOTEBOOKS_DIR.parent
DATA_DIR = BASE_DIR / "data"

# Estructura de carpetas de datos
RAW_DATA = DATA_DIR / "raw"
PROCESSED_DATA = DATA_DIR / "processed"
CARGA_DIR = RAW_DATA / "Carga de datos"

# Archivos específicos (Single Source of Truth)
rutas_archivos = {
    "gpkg": CARGA_DIR / "geodatabase_proyecto.gpkg",
    "censo_csv": CARGA_DIR / "censo_RM_totales_comuna.csv",
    "censo_excel": CARGA_DIR / "D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx"
}

# Carpetas de salida
OUTPUTS_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Crear directorios si no existen
for d in [RAW_DATA, PROCESSED_DATA, FIGURES_DIR, REPORTS_DIR, CARGA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Exportar variables globales para uso fácil
RUTA_GPKG = rutas_archivos["gpkg"]
RUTA_CENSO_CSV = rutas_archivos["censo_csv"]

# ============================================================================
# 2. FUNCIONES AUXILIARES
# ============================================================================

def print_status():
    """Imprime el estado de la configuración actual."""
    print("===  Template PEP1 Configurado Exitosamente ===")
    print(f" Base Dir       : {BASE_DIR}")
    print(f" GeoDatabase    : {' Encontrada' if RUTA_GPKG.exists() else ' No encontrada'}")
    print(f" Censo CSV      : {' Encontrado' if RUTA_CENSO_CSV.exists() else ' No encontrado'}")
    print("=================================================")

def load_geodata(path: Path, layer: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
    """
    Carga datos geoespaciales de forma robusta.
    
    Args:
        path (Path): Ruta al archivo.
        layer (str, optional): Nombre de la capa (necesario para GPKG).
    """
    if not path.exists():
        print(f" Error: El archivo no existe -> {path}")
        return None

    try:
        if layer:
            gdf = gpd.read_file(path, layer=layer)
            info_msg = f"Capa '{layer}'"
        else:
            gdf = gpd.read_file(path)
            info_msg = "Archivo"
            
        print(f" Cargado {info_msg}: {len(gdf)} registros | CRS: {gdf.crs}")
        return gdf
    except Exception as exc:
        print(f" Error crítico al cargar {path}: {exc}")
        return None

def save_figure(fig, name: str, subdir: Optional[str] = None, dpi: int = 300):
    """
    Guarda una figura en alta resolución.
    
    Args:
        fig: Objeto figura de matplotlib.
        name: Nombre del archivo (sin extensión).
        subdir: Carpeta opcional dentro de 'figures'.
        dpi: Puntos por pulgada (300 es calidad impresión).
    """
    out_dir = FIGURES_DIR / subdir if subdir else FIGURES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / f"{name}.png"
    
    # Metadata para el archivo
    metadata = {"Creator": "Grupo 1 Geoinformática"}
    
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", metadata=metadata)
    print(f"  Imagen guardada: {out_path.name}")

# ============================================================================
# 3. EJECUCIÓN INICIAL
# ============================================================================

if __name__ == "__main__" or "get_ipython" in globals():
    # Solo ejecutar el print de estado si se corre directamente o en Jupyter
    print_status()