from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ============================================================================
# 1. RUTAS DEL PROYECTO
# ============================================================================

# Este archivo vive en: BASE_DIR / "notebooks" / "00_template.py"
NOTEBOOKS_DIR = Path(__file__).resolve().parent
BASE_DIR = NOTEBOOKS_DIR.parent   # carpeta "Desiertos"

DATA_DIR = BASE_DIR / "data"
RAW_DATA = DATA_DIR / "raw"

# 👇 carpeta donde está TODO lo de PEP1 (tal como dijiste)
CARGA_DIR = RAW_DATA / "Carga de datos"

# Archivos principales dentro de "Carga de datos"
RUTA_GPKG = CARGA_DIR / "geodatabase_proyecto.gpkg"
RUTA_CENSO_CSV = CARGA_DIR / "censo_RM_totales_comuna.csv"
RUTA_EXCEL_CENSO = CARGA_DIR / "D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx"

PROCESSED_DATA = DATA_DIR / "processed"

OUTPUTS_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

for d in [RAW_DATA, PROCESSED_DATA, FIGURES_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("=== Template PEP1 Desiertos cargado ===")
print("BASE_DIR        :", BASE_DIR)
print("CARGA_DIR       :", CARGA_DIR)
print("RUTA_GPKG       :", RUTA_GPKG)
print("RUTA_CENSO_CSV  :", RUTA_CENSO_CSV)

# ============================================================================
# 2. FUNCIONES AUXILIARES
# ============================================================================

def load_geodata(path: Path) -> gpd.GeoDataFrame | None:
    """Carga un archivo geoespacial (SHP, GeoJSON, GPKG, etc.)."""
    try:
        gdf = gpd.read_file(path)
        print(f"✅ Cargado: {path} ({len(gdf)} filas)")
        return gdf
    except Exception as exc:
        print(f"⚠️ Error al cargar {path}: {exc}")
        return None


def save_figure(fig, name: str, subdir: str | None = None, dpi: int = 150):
    """Guarda una figura en outputs/figures."""
    out_dir = FIGURES_DIR / subdir if subdir else FIGURES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"💾 Figura guardada en: {out_path}")


# ============================================================================
# 3. ESTILO GRÁFICO
# ============================================================================

plt.style.use("default")
sns.set_theme(style="whitegrid")

