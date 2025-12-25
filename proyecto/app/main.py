import textwrap
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from folium import plugins
from streamlit_folium import st_folium
import streamlit as st


# ----------------------------------------------------------------------
# Rutas base del proyecto
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_RAW = BASE_DIR / "data" / "raw" / "Carga de datos"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

RUTA_GPKG = DATA_RAW / "geodatabase_proyecto.gpkg"
CATALOGO_PATH = DATA_PROCESSED / "catalogo_capas_geodatabase.csv"
INDICADORES_PATH = DATA_PROCESSED / "indicadores_servicios.csv"
ACCESIBILIDAD_PATH = DATA_PROCESSED / "accesibilidad_servicios.csv"
DESIERTOS_PATH = DATA_PROCESSED / "desiertos_servicios.csv"

LAYER_COMUNAS = "comunas_rm_censo"


# ----------------------------------------------------------------------
# Funciones de carga (cacheadas)
# ----------------------------------------------------------------------
@st.cache_data
def cargar_geodataframe(layer_name: str) -> gpd.GeoDataFrame:
    if not RUTA_GPKG.exists():
        raise FileNotFoundError(f"No se encontró el GeoPackage: {RUTA_GPKG}")
    return gpd.read_file(RUTA_GPKG, layer=layer_name)


@st.cache_data
def cargar_catalogo() -> pd.DataFrame:
    if CATALOGO_PATH.exists():
        return pd.read_csv(CATALOGO_PATH)
    return pd.DataFrame()


@st.cache_data
def cargar_indicadores() -> pd.DataFrame:
    if INDICADORES_PATH.exists():
        return pd.read_csv(INDICADORES_PATH)
    return pd.DataFrame()


@st.cache_data
def cargar_accesibilidad() -> pd.DataFrame:
    if ACCESIBILIDAD_PATH.exists():
        return pd.read_csv(ACCESIBILIDAD_PATH)
    return pd.DataFrame()


@st.cache_data
def cargar_desiertos() -> pd.DataFrame:
    if DESIERTOS_PATH.exists():
        return pd.read_csv(DESIERTOS_PATH)
    return pd.DataFrame()


@st.cache_data
def cargar_capas_puntos() -> dict[str, gpd.GeoDataFrame]:
    """
    Carga todas las capas de puntos desde el GeoPackage.

    Returns
    -------
    dict[str, gpd.GeoDataFrame]
        Diccionario con nombre de capa como clave y GeoDataFrame como valor.
    """
    capas_puntos = [
        "companias_bomberos",
        "cuarteles_carabineros",
        "establecimientos_educacion",
        "establecimientos_educacion_superior",
        "establecimientos_salud",
        "infraestructura_deportiva",
        "municipios",
        "paradas_metro_tren",
    ]
    capas = {}
    for capa in capas_puntos:
        try:
            capas[capa] = cargar_geodataframe(capa)
        except Exception as e:
            st.warning(f"No se pudo cargar la capa {capa}: {e}")
    return capas


# ----------------------------------------------------------------------
# Configuración general de la página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="PEP1 – Desiertos de Servicio RM",
    layout="wide",
)


# ----------------------------------------------------------------------
# Sidebar: navegación
# ----------------------------------------------------------------------
st.sidebar.title("PEP1 – Desiertos de servicios")
seccion = st.sidebar.radio(
    "Secciones",
    [
        "Introducción y datos",
        "Oferta de servicios",
        "Accesibilidad",
        "Desiertos de servicio",
        "Mapa Interactivo de Puntos",
    ],
)


# ----------------------------------------------------------------------
# Sección 1: Introducción y datos
# ----------------------------------------------------------------------
if seccion == "Introducción y datos":
    st.title("PEP1 – Desiertos de servicios en la Región Metropolitana")

    st.subheader("Objetivo general")
    st.write(
        textwrap.dedent(
            """
            El objetivo de este trabajo es caracterizar la distribución territorial de servicios 
            relevantes en la Región Metropolitana y detectar desiertos de servicio a escala comunal,
            combinando oferta relativa, accesibilidad espacial y cobertura.
            """
        )
    )

    st.subheader("Metodología general")
    st.markdown(
        """
        1. **Construcción de geodatabase** a partir de:
           - Censo 2017 (población por comuna).
           - Capas IDE Chile (salud, educación, ferias, áreas verdes, etc.).
           - Datos OSM y GTFS (paradas, supermercados, equipamientos).
        2. **Cálculo de indicadores de oferta** por comuna:
           - Conteos de servicios.
           - Tasas por 10.000 habitantes.
        3. **Cálculo de accesibilidad espacial**:
           - Distancia mínima desde cada comuna al servicio más cercano.
           - Cobertura de superficie comunal mediante buffers.
        4. **Definición de desiertos de servicio**:
           - Umbrales estadísticos sobre oferta, distancias y cobertura.
           - Índices por servicio e índice agregado por comuna.
        """
    )

    st.subheader("Geodatabase del proyecto")

    comunas = cargar_geodataframe(LAYER_COMUNAS)
    catalogo = cargar_catalogo()

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("**Vista general de la capa de comunas (RM)**")
        fig, ax = plt.subplots(figsize=(5, 5))
        comunas.boundary.plot(ax=ax, color="black", linewidth=0.4)
        ax.set_axis_off()
        ax.set_title("Comunas Región Metropolitana")
        st.pyplot(fig)

    with col2:
        st.markdown("**Capas disponibles en geodatabase_proyecto.gpkg**")
        if not catalogo.empty:
            st.dataframe(catalogo)
        else:
            st.info("No se encontró el catálogo de capas. Revise notebooks 00–01.")

    st.markdown("---")
    st.markdown("**Notas técnicas**")
    st.markdown(
        f"""
        - Directorio base del proyecto: `{BASE_DIR}`
        - Geodatabase: `{RUTA_GPKG}`
        - CRS de trabajo: `EPSG:32719` (UTM 19S, metros).
        """
    )


# ----------------------------------------------------------------------
# Sección 2: Oferta de servicios
# ----------------------------------------------------------------------
elif seccion == "Oferta de servicios":
    st.title("Oferta de servicios por comuna")

    indicadores = cargar_indicadores()
    comunas = cargar_geodataframe(LAYER_COMUNAS)

    if indicadores.empty:
        st.warning(
            "No se encontraron datos de indicadores. Ejecute los notebooks para generar los datos procesados."
        )
        st.info(
            "Ejecuta los notebooks en orden: 01_data_acquisition.ipynb → 02_exploratory_analysis.ipynb → 03_geostatistics.ipynb → 04_machine_learning.ipynb → 05_results_synthesis.ipynb"
        )
        st.stop()

    # Servicios que tienen tasas por 10k habitantes
    servicios_disponibles = {
        "Establecimientos de salud": "tasa_establecimientos_salud_x10k",
        "Establecimientos de educación escolar": "tasa_establecimientos_educacion_x10k",
        "Establecimientos de educación superior": "tasa_establecimientos_educacion_superior_x10k",
        "Supermercados (OSM)": "tasa_osm_supermercados_x10k",
        "Almacenes de barrio (OSM)": "tasa_osm_almacenes_barrio_x10k",
    }

    nombre_servicio = st.selectbox(
        "Seleccionar servicio",
        list(servicios_disponibles.keys()),
    )
    col_tasa = servicios_disponibles[nombre_servicio]

    if col_tasa not in indicadores.columns:
        st.error(f"No se encontró la columna {col_tasa} en indicadores_servicios.csv.")
    else:
        st.subheader("Tabla resumen")

        df_tabla = indicadores[["comuna", "poblacion", col_tasa]].copy()
        df_tabla = df_tabla.rename(
            columns={
                "poblacion": "población",
                col_tasa: "tasa_x10k",
            }
        )
        df_tabla_ord = df_tabla.sort_values("tasa_x10k")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Comunas con menor tasa por 10.000 habitantes**")
            st.dataframe(df_tabla_ord.head(10))

        with col2:
            st.markdown("**Comunas con mayor tasa por 10.000 habitantes**")
            st.dataframe(df_tabla_ord.tail(10))

        st.subheader("Mapa coroplético de oferta relativa")

        comunas_ind = comunas.merge(
            indicadores[["cod_comuna", col_tasa]],
            left_on="CUT_COM",
            right_on="cod_comuna",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        comunas_ind.plot(
            column=col_tasa,
            ax=ax,
            legend=True,
            cmap="Blues",
            edgecolor="black",
            linewidth=0.3,
        )
        ax.set_axis_off()
        ax.set_title(f"{nombre_servicio} por 10.000 habitantes", fontsize=12)
        st.pyplot(fig)


# ----------------------------------------------------------------------
# Sección 3: Accesibilidad
# ----------------------------------------------------------------------
elif seccion == "Accesibilidad":
    st.title("Accesibilidad a servicios")

    accesibilidad = cargar_accesibilidad()
    comunas = cargar_geodataframe(LAYER_COMUNAS)

    if accesibilidad.empty:
        st.warning(
            "No se encontraron datos de accesibilidad. Ejecute los notebooks para generar los datos procesados."
        )
        st.info(
            "Ejecuta los notebooks en orden: 01_data_acquisition.ipynb → 02_exploratory_analysis.ipynb → 03_geostatistics.ipynb → 04_machine_learning.ipynb → 05_results_synthesis.ipynb"
        )
        st.stop()

    st.markdown(
        """
        Se utilizan dos tipos de métricas de accesibilidad por comuna:
        
        - **Distancia mínima** desde el centroide comunal al servicio más cercano (km).
        - **Cobertura territorial**: porcentaje de superficie comunal dentro de un radio definido alrededor de los servicios.
        """
    )

    # Definición de columnas esperadas
    opciones = {
        "Salud": {
            "dist_col": "dist_min_salud_km",
            "cov_col": "porc_cubierto_salud",
        },
        "Supermercados": {
            "dist_col": "dist_min_supermercados_km",
            "cov_col": "porc_cubierto_supermercados",
        },
    }

    servicio_sel = st.selectbox("Seleccionar servicio", list(opciones.keys()))
    cols = opciones[servicio_sel]

    dist_col = cols["dist_col"]
    cov_col = cols["cov_col"]

    if dist_col not in accesibilidad.columns or cov_col not in accesibilidad.columns:
        st.error(
            f"Faltan columnas de accesibilidad para {servicio_sel}. "
            f"Revise notebooks 03 y archivos en data/processed."
        )
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Comunas más alejadas del servicio (distancia mínima)**")
            df_dist = accesibilidad[["comuna", dist_col]].sort_values(
                dist_col, ascending=False
            )
            df_dist = df_dist.rename(columns={dist_col: "distancia_km"})
            st.dataframe(df_dist.head(10))

        with col2:
            st.markdown("**Comunas con menor cobertura territorial del servicio**")
            df_cov = accesibilidad[["comuna", cov_col]].sort_values(
                cov_col, ascending=True
            )
            df_cov = df_cov.rename(columns={cov_col: "porcentaje_cubierto"})
            st.dataframe(df_cov.head(10))

        st.subheader("Mapa: distancia mínima al servicio")

        comunas_dist = comunas.merge(
            accesibilidad[["cod_comuna", dist_col]],
            left_on="CUT_COM",
            right_on="cod_comuna",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        comunas_dist.plot(
            column=dist_col,
            ax=ax,
            legend=True,
            cmap="OrRd",
            edgecolor="black",
            linewidth=0.3,
        )
        ax.set_axis_off()
        ax.set_title(f"Distancia mínima a {servicio_sel.lower()} (km)", fontsize=12)
        st.pyplot(fig)

        st.subheader("Mapa: porcentaje de superficie comunal cubierta")

        comunas_cov = comunas.merge(
            accesibilidad[["cod_comuna", cov_col]],
            left_on="CUT_COM",
            right_on="cod_comuna",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        comunas_cov.plot(
            column=cov_col,
            ax=ax,
            legend=True,
            cmap="Greens",
            edgecolor="black",
            linewidth=0.3,
        )
        ax.set_axis_off()
        ax.set_title(
            f"Porcentaje de superficie comunal cubierta por {servicio_sel.lower()}",
            fontsize=12,
        )
        st.pyplot(fig)


# ----------------------------------------------------------------------
# Sección 4: Desiertos de servicio
# ----------------------------------------------------------------------
elif seccion == "Desiertos de servicio":
    st.title("Desiertos de servicio")

    desiertos = cargar_desiertos()
    comunas = cargar_geodataframe(LAYER_COMUNAS)

    if desiertos.empty:
        st.warning(
            "No se encontraron datos de desiertos de servicio. Ejecute los notebooks para generar los datos procesados."
        )
        st.info(
            "Ejecuta los notebooks en orden: 01_data_acquisition.ipynb → 02_exploratory_analysis.ipynb → 03_geostatistics.ipynb → 04_machine_learning.ipynb → 05_results_synthesis.ipynb"
        )
        st.stop()

    st.markdown(
        """
        A partir de los indicadores de oferta y accesibilidad se construyó, 
        para cada comuna, un índice de desiertos de servicio. 
        
        La lógica es:
        
        - Baja oferta relativa (tasas bajas).
        - Alta distancia al servicio más cercano.
        - Baja cobertura territorial.
        
        Cuando una comuna cumple varias de estas condiciones para un servicio,
        se clasifica como desierto de servicio para ese equipamiento.
        """
    )

    if "n_servicios_en_desierto" not in desiertos.columns:
        st.error(
            "La columna 'n_servicios_en_desierto' no está disponible en desiertos_servicios.csv. "
            "Revise el Notebook 04."
        )
    else:
        st.subheader("Ranking comunas más críticas")

        cols_rank = ["cod_comuna", "comuna", "poblacion", "n_servicios_en_desierto"]
        cols_rank = [c for c in cols_rank if c in desiertos.columns]

        ranking = desiertos[cols_rank].sort_values(
            "n_servicios_en_desierto", ascending=False
        )
        st.dataframe(ranking.head(15))

        st.subheader("Mapa índice de desiertos")

        comunas_desiertos = comunas.merge(
            desiertos[["cod_comuna", "n_servicios_en_desierto"]],
            left_on="CUT_COM",
            right_on="cod_comuna",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        comunas_desiertos.plot(
            column="n_servicios_en_desierto",
            ax=ax,
            legend=True,
            cmap="Reds",
            edgecolor="black",
            linewidth=0.3,
        )
        ax.set_axis_off()
        ax.set_title(
            "Número de servicios en condición de desierto por comuna", fontsize=12
        )
        st.pyplot(fig)

        # Si existen banderas específicas por servicio, las mostramos
        banderas = [c for c in desiertos.columns if c.startswith("es_desierto_")]

        if banderas:
            st.subheader("Desiertos por tipo de servicio")
            st.markdown(
                "1 indica que la comuna se clasifica como desierto para ese servicio, 0 indica que no."
            )
            st.dataframe(
                desiertos[
                    ["cod_comuna", "comuna", "poblacion", "n_servicios_en_desierto"]
                    + banderas
                ].sort_values("n_servicios_en_desierto", ascending=False)
            )


# ----------------------------------------------------------------------
# Sección 5: Mapa Interactivo de Puntos
# ----------------------------------------------------------------------
elif seccion == "Mapa Interactivo de Puntos":
    st.title("Mapa Interactivo de Puntos de Servicios")

    capas_puntos = cargar_capas_puntos()

    if not capas_puntos:
        st.warning("No se pudieron cargar las capas de puntos.")
        st.stop()

    # Crear mapa Folium centrado en RM (aprox. Santiago)
    m = folium.Map(location=[-33.45, -70.65], zoom_start=10)

    # Colores para cada capa
    colores = {
        "companias_bomberos": "red",
        "cuarteles_carabineros": "blue",
        "establecimientos_educacion": "green",
        "establecimientos_educacion_superior": "purple",
        "establecimientos_salud": "orange",
        "infraestructura_deportiva": "pink",
        "municipios": "black",
        "paradas_metro_tren": "gray",
        "paradas_micro": "brown",
    }

    # Agregar capas al mapa
    for nombre_capa, gdf in capas_puntos.items():
        if gdf.empty:
            continue
        color = colores.get(nombre_capa, "blue")
        # Convertir a WGS84 para Folium
        gdf_wgs84 = gdf.to_crs("EPSG:4326")
        # Filtrar geometrías vacías
        gdf_wgs84 = gdf_wgs84[~gdf_wgs84.geometry.is_empty]
        for _, row in gdf_wgs84.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=3,
                color=color,
                fill=True,
                fill_color=color,
                popup=nombre_capa,
            ).add_to(m)

    # Agregar plugin de pantalla completa
    plugins.Fullscreen().add_to(m)

    # Mostrar mapa en Streamlit
    st_folium(m, width=700, height=500)
