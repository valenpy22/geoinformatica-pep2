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
import calculator_backend as calc
from streamlit_option_menu import option_menu


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


# Función wrapper (SIN caché para que chequee siempre el mtime)
def cargar_accesibilidad() -> pd.DataFrame:
    # Usamos desiertos_servicios.csv como fuente principal de accesibilidad 
    # ya que es la tabla maestra procesada con todos los datos finales.
    return cargar_desiertos()




# Función wrapper (SIN caché)
def cargar_desiertos() -> pd.DataFrame:
    """
    Acceso público a datos de desiertos con validación de mtime para consistencia.
    """
    if not DESIERTOS_PATH.exists():
        return pd.DataFrame()
        
    mtime = DESIERTOS_PATH.stat().st_mtime
    
    # Manejamos el archivo de indicadores como dependencia opcional para el caché
    meta_mtime = None
    if INDICADORES_PATH.exists():
        meta_mtime = INDICADORES_PATH.stat().st_mtime
        
    return _load_desiertos_content(DESIERTOS_PATH, mtime, INDICADORES_PATH, meta_mtime)

# Función worker (CON caché)
@st.cache_data
def _load_desiertos_content(path: Path, _mtime: float, meta_path: Path = None, _meta_mtime: float = None) -> pd.DataFrame:
    """
    Carga el CSV de desiertos y lo enriquece de forma segura con población.
    La firma de la función incluye _meta_mtime para que Streamlit invalide
    el caché si el archivo de indicadores cambia.
    """
    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"Error al leer el archivo de desiertos en {path.name}: {e}")
        return pd.DataFrame()

    # Enriquecimiento reactivo: solo si falta la columna 'poblacion'
    if "poblacion" not in df.columns and meta_path and meta_path.exists():
        try:
            indicadores = pd.read_csv(meta_path)
            # Validación de contrato: cod_comuna para el join y poblacion para el dato
            if {"cod_comuna", "poblacion"}.issubset(indicadores.columns):
                df = df.merge(
                    indicadores[["cod_comuna", "poblacion"]],
                    on="cod_comuna",
                    how="left"
                )
        except Exception as e:
            # Fallback silencioso en UI pero logueado en consola
            print(f"Aviso: No se pudo enriquecer con población desde {meta_path.name}: {e}")
            
    return df


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


# Wrapper (SIN caché)
def cargar_html_template(template_name: str) -> str:
    """
    Carga un template HTML desde el directorio views.
    Usa caché pero se invalida automáticamente si el archivo cambia.
    """
    template_path = Path(__file__).parent / "views" / template_name
    mtime = template_path.stat().st_mtime
    return _load_template_content(template_path, mtime)

# Worker (CON caché)
@st.cache_data
def _load_template_content(path: Path, _mtime: float) -> str:
    """Helper function que realmente lee el archivo."""
    return path.read_text(encoding="utf-8")


# ----------------------------------------------------------------------
# Configuración general de la página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="PEP1 – Desiertos de Servicio RM",
    layout="wide",
)


# ----------------------------------------------------------------------
# Sidebar: navegación con option_menu
# ----------------------------------------------------------------------
with st.sidebar:
    # Cargar título desde template HTML (con caché)
    st.markdown(cargar_html_template("sidebar_header.html"), unsafe_allow_html=True)

    seccion = option_menu(
        menu_title=None,  # Sin título adicional
        options=[
            "Introducción y datos",
            "Oferta de Servicios",
            "Accesibilidad",
            "Desiertos de Servicio",
            "Mapa Interactivo de Puntos",
            "Calculadora Calidad de Vida",
        ],
        icons=[
            "house-door",
            "bar-chart",
            "geo-alt",
            "exclamation-triangle",
            "map",
            "calculator",
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "transparent",
            },
            "icon": {
                "color": "#b6bac2", 
                "font-size": "18px",
            },
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "2px 0px",
                "padding": "12px 16px",
                "border-radius": "8px",
                "color": "#4a5568",  # Texto más claro pero legible
                "--hover-color": "#e8f4f8",  # Azul muy claro al hover
                "transition": "all 0.3s ease",
            },
            "nav-link-selected": {
                "background-color": "#3b82f6",  # Azul más brillante y moderno
                "color": "white",
                "font-weight": "500",
                "box-shadow": "0 2px 8px rgba(59,130,246,0.3)",
            },
            "icon-selected": {
                "color": "white",  # Iconos blancos cuando está seleccionado
            },
        },
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
            # Renombrar columnas para mejor visualización
            catalogo_display = catalogo.rename(columns={
                "capa": "Capa",
                "n_registros": "N° Registros",
                "tipo_geometria": "Tipo Geometría",
                "crs": "Sistema de Coordenadas"
            })
            st.dataframe(catalogo_display, use_container_width=True)
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
# Sección 2: Oferta de Servicios
# ----------------------------------------------------------------------
elif seccion == "Oferta de Servicios":
    st.title("Oferta de Servicios por Comuna")

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
        "Seleccionar Servicio",
        list(servicios_disponibles.keys()),
    )
    col_tasa = servicios_disponibles[nombre_servicio]

    if col_tasa not in indicadores.columns:
        st.error(f"No se encontró la columna {col_tasa} en indicadores_servicios.csv.")
    else:
        st.subheader("Tabla Resumen")

        df_tabla = indicadores[["comuna", "poblacion", col_tasa]].copy()
        df_tabla = df_tabla.rename(
            columns={
                "comuna": "Comuna",
                "poblacion": "Población",
                col_tasa: "Tasa x 10k hab.",
            }
        )
        df_tabla_ord = df_tabla.sort_values("Tasa x 10k hab.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Comunas con menor tasa por 10.000 habitantes**")
            st.dataframe(df_tabla_ord.head(10), use_container_width=True)

        with col2:
            st.markdown("**Comunas con mayor tasa por 10.000 habitantes**")
            st.dataframe(df_tabla_ord.tail(10), use_container_width=True)

        st.subheader("Mapa Coroplético de Oferta Relativa")

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
    st.title("Accesibilidad a Servicios")

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
        Se utiliza el motor **OpenTripPlanner (OTP)** para calcular la accesibilidad real 
        utilizando la red de transporte público y caminata:
        
        - **Tiempo de viaje**: Minutos necesarios para llegar desde el centroide comunal al servicio más cercano.
        - **Modos**: Combinación de Caminata + Bus/Metro (GTFS).
        """
    )

    # Definición de las categorías disponibles basadas en los datos reales de desiertos_servicios.csv
    opciones = {
        "Salud": "salud",
        "Educación Escolar": "educacion_escolar",
        "Educación Superior": "educacion_superior",
        "Supermercados": "supermercados",
        "Almacenes de Barrio": "almacenes_barrio",
        "Áreas Verdes": "areas_verdes",
        "Bancos": "bancos",
        "Bomberos": "bomberos",
        "Carabineros": "carabineros",
        "Paradas de Micro": "micro",
        "Metro y Tren": "metro_tren",
        "Infraestructura Deportiva": "deporte_infra",
        "Ferias Libres": "ferias_libres",
    }
    
    servicio_sel = st.selectbox("Seleccionar Servicio", list(opciones.keys()))
    metric_col = opciones[servicio_sel]

    if metric_col not in accesibilidad.columns:
        st.error(
            f"Faltan datos de accesibilidad para {servicio_sel} ({metric_col}). "
            f"Asegúrese de haber ejecutado todos los pasos del Notebook 04."
        )
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Comunas con mayor tiempo de viaje a {servicio_sel}**")
            # Filtrar nulos si existen para el ranking
            df_dist = accesibilidad[["comuna", metric_col]].dropna().sort_values(
                metric_col, ascending=False
            )
            df_dist = df_dist.rename(columns={
                "comuna": "Comuna",
                metric_col: "Tiempo (min)"
            })
            st.dataframe(df_dist.head(10), use_container_width=True)

        with col2:
            st.markdown(f"**Comunas con mejor acceso a {servicio_sel}**")
            df_cov = accesibilidad[["comuna", metric_col]].dropna().sort_values(
                metric_col, ascending=True
            )
            df_cov = df_cov.rename(columns={
                "comuna": "Comuna",
                metric_col: "Tiempo (min)"
            })
            st.dataframe(df_cov.head(10), use_container_width=True)

        st.subheader(f"Mapa: Tiempo de viaje a {servicio_sel} (OTP)")

        comunas_dist = comunas.merge(
            accesibilidad[["cod_comuna", metric_col]],
            left_on="CUT_COM",
            right_on="cod_comuna",
            how="left",
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        comunas_dist.plot(
            column=metric_col,
            ax=ax,
            legend=True,
            cmap="OrRd",
            edgecolor="black",
            linewidth=0.3,
            missing_kwds={"color": "lightgrey", "label": "Sin datos"}
        )
        ax.set_axis_off()
        ax.set_title(f"Tiempo de viaje a {servicio_sel} (minutos)", fontsize=12)
        st.pyplot(fig)


# ----------------------------------------------------------------------
# Sección 4: Desiertos de Servicio
# ----------------------------------------------------------------------
elif seccion == "Desiertos de Servicio":
    st.title("Desiertos de Servicio")

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
        
        # Renombrar columnas para mejor visualización
        ranking_display = ranking.rename(columns={
            "cod_comuna": "Código Comuna",
            "comuna": "Comuna",
            "poblacion": "Población",
            "n_servicios_en_desierto": "N° Servicios en Desierto"
        })
        st.dataframe(ranking_display.head(15), use_container_width=True)

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
            
            cols_detalle = ["cod_comuna", "comuna", "poblacion", "n_servicios_en_desierto"]
            cols_detalle = [c for c in cols_detalle if c in desiertos.columns] + banderas

            desiertos_detalle = desiertos[cols_detalle].sort_values(
                "n_servicios_en_desierto", ascending=False
            )
            
            # Renombrar columnas base
            rename_dict = {
                "cod_comuna": "Código Comuna",
                "comuna": "Comuna",
                "poblacion": "Población",
                "n_servicios_en_desierto": "N° Servicios en Desierto"
            }
            
            # Renombrar banderas (es_desierto_xxx -> Desierto: Xxx)
            for col in banderas:
                servicio_name = col.replace("es_desierto_", "").replace("_", " ").title()
                rename_dict[col] = f"Desierto: {servicio_name}"
            
            desiertos_display = desiertos_detalle.rename(columns=rename_dict)
            st.dataframe(desiertos_display, use_container_width=True)


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


# ----------------------------------------------------------------------
# Sección 6: Calculadora Calidad de Vida
# ----------------------------------------------------------------------
elif seccion == "Calculadora Calidad de Vida":
    st.title("🧮 Calculadora de Calidad de Vida")
    st.markdown("""
    Esta herramienta calcula un índice de calidad de vida (0-100) para una ubicación específica en la Región Metropolitana,
    personalizado según el perfil del usuario (Estudiante, Adulto Mayor, Familia Joven).
    """)

    # Inicializar estado para coordenadas si no existe
    if "lat_calc" not in st.session_state:
        st.session_state.lat_calc = -33.4372
    if "lon_calc" not in st.session_state:
        st.session_state.lon_calc = -70.6506

    # 1. Cargar datos unificados
    with st.spinner("Cargando motor de cálculo y base de datos de servicios..."):
        gdf_servicios = calc.cargar_servicios_unificados(RUTA_GPKG)
        if gdf_servicios.empty:
            st.error("No se pudieron cargar los servicios. Verifique geodatabase_proyecto.gpkg")
            st.stop()

    col_config, col_map = st.columns([1, 2])

    with col_config:
        st.subheader("1. Configuración")
        
        # Selector de Perfil
        perfil_sel = st.selectbox(
            "Seleccione Perfil", 
            list(calc.PERFILES_USUARIO.keys()),
            format_func=lambda x: x.replace("_", " ").title()
        )
        desc = calc.PERFILES_USUARIO[perfil_sel]["desc"]
        st.info(f"💡 **Enfoque**: {desc}")

    with col_map:
        st.subheader("Mapa de Selección")
        # Usamos las coordenadas del estado para centrar
        # Nota: lat_val/lon_val aún no existen como variables locales de input, usamos session_state directo
        curr_lat = st.session_state.lat_calc
        curr_lon = st.session_state.lon_calc
        
        # Crear mapa centrado en la selección actual
        m = folium.Map(location=[curr_lat, curr_lon], zoom_start=14)
        
        # Marcador en la posición actual
        folium.Marker(
            [curr_lat, curr_lon], 
            popup="Ubicación Objetivo",
            icon=folium.Icon(color="red", icon="star")
        ).add_to(m)
        
        # Círculo de radio 1000m (para referencia visual)
        folium.Circle(
            location=[curr_lat, curr_lon],
            radius=1000,
            color="blue",
            fill=True,
            fill_opacity=0.1
        ).add_to(m)

        # Capturar clics
        # Usamos una key dinámica para forzar al mapa a redibujarse cuando cambian las coordenadas
        # Esto asegura que el marcador y el centro se actualicen visualmente.
        map_key = f"mapa_calc_{curr_lat}_{curr_lon}"
        map_data = st_folium(m, width="100%", height=500, key=map_key)

        # Lógica de actualización por clic
        if map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lng = map_data["last_clicked"]["lng"]
            
            # Si cambia respecto a lo guardado, actualizamos y recargamos
            if abs(click_lat - st.session_state.lat_calc) > 0.0001 or abs(click_lng - st.session_state.lon_calc) > 0.0001:
                st.session_state.lat_calc = click_lat
                st.session_state.lon_calc = click_lng
                # Actualizar también los inputs directamente (ahora es seguro porque inputs no se han creado aún)
                st.session_state.input_lat = click_lat
                st.session_state.input_lon = click_lng
                st.rerun()

    with col_config:
        st.divider()

        st.subheader("2. Ubicación")
        st.markdown("Haga clic en el mapa o ajuste las coordenadas:")
        
        # Callback para cuando el usuario edita manual
        def update_coords():
            st.session_state.lat_calc = st.session_state.input_lat
            st.session_state.lon_calc = st.session_state.input_lon

        lat_val = st.number_input("Latitud", value=st.session_state.lat_calc, format="%.5f", key="input_lat", on_change=update_coords)
        lon_val = st.number_input("Longitud", value=st.session_state.lon_calc, format="%.5f", key="input_lon", on_change=update_coords)
        
        # Botón Calcular
        st.divider()
        btn_calcular = st.button("🚀 Calcular Índice", type="primary", use_container_width=True)



    # RESULTADOS
    if btn_calcular:
        st.markdown("---")
        res = calc.calcular_indice_calidad_vida(gdf_servicios, lat_val, lon_val, perfil_sel)
        
        if "error" in res:
            st.error(res["error"])
        else:
            score = res["indice"]
            detalles = res["detalles"]
            
            # Header de resultados
            c_score, c_msg = st.columns([1, 3])
            with c_score:
                st.metric("Índice Calidad de Vida", f"{score}/100")
            with c_msg:
                if score >= 80:
                    st.success("🌟 **Excelente ubicación** para este perfil.")
                elif score >= 50:
                    st.warning("⚠️ **Ubicación regular**, tiene carencias.")
                else:
                    st.error("🛑 **Zona deficiente** para las necesidades de este perfil.")
            
            st.subheader("📊 Desglose del Puntaje")
            
            if detalles:
                # Preparamos datos para visualización
                rows = []
                for srv, val in detalles.items():
                    rows.append({
                        "Servicio": srv,
                        "Conteo": val["conteo"],
                        "Importancia (1-5)": val["importancia"],
                        "Aporte Puntos": val["aporte_final"],
                        "Score Norm": val["score_norm"]
                    })
                df_res = pd.DataFrame(rows).sort_values("Aporte Puntos", ascending=False)
                
                tab_tabla, tab_grafico = st.tabs(["Tabla Detallada", "Gráfico de Aporte"])
                
                with tab_tabla:
                    st.dataframe(
                        df_res.style.background_gradient(subset=["Aporte Puntos"], cmap="Greens"),
                        use_container_width=True
                    )
                
                with tab_grafico:
                    st.bar_chart(df_res.set_index("Servicio")["Aporte Puntos"])
            else:
                st.info("No se encontraron servicios que aporten puntaje en este radio de 1000m.")
