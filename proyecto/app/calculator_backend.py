import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import Point

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SERVICE_LAYERS = {
    "salud": "establecimientos_salud",
    "educacion_escolar": "establecimientos_educacion",
    "educacion_superior": "establecimientos_educacion_superior",
    "supermercados": "osm_supermercados",
    "almacenes_barrio": "osm_almacenes_barrio",
    "bancos": "osm_bancos",
    "ferias_libres": "ferias_libres",
    "areas_verdes": "areas_verdes",
    "cuarteles_carabineros": "cuarteles_carabineros",
    "companias_bomberos": "companias_bomberos",
    "estadios": "osm_estadios",
    "malls": "osm_malls",
    "bencineras": "osm_bencineras",
    "iglesias": "osm_iglesias",
    "museos": "osm_museos",
    "infraestructura_deportiva": "infraestructura_deportiva",
    "paradas_micro": "paradas_micro",
    "paradas_metro_tren": "paradas_metro_tren",
}

SCORING_CONFIG = {
    # Transporte
    "paradas_metro_tren": {"meta": 2, "desc": "Acceso a red principal"},
    "paradas_micro": {"meta": 5, "desc": "Opciones de recorridos"},
    # Salud y Seguridad
    "salud": {"meta": 2, "desc": "Consultorios/Centros Médicos"},
    "cuarteles_carabineros": {"meta": 1, "desc": "Seguridad cercana"},
    "companias_bomberos": {"meta": 1, "desc": "Respuesta emergencia"},
    # Educación
    "educacion_escolar": {"meta": 3, "desc": "Opciones colegios"},
    "educacion_superior": {"meta": 1, "desc": "Acceso a educación sup."},
    # Abastecimiento
    "supermercados": {"meta": 2, "desc": "Competencia precios"},
    "almacenes_barrio": {"meta": 4, "desc": "Comercio local"},
    "ferias_libres": {"meta": 1, "desc": "Productos frescos"},
    "bencineras": {"meta": 2, "desc": "Abastecimiento auto"},
    # Calidad de Vida
    "areas_verdes": {"meta": 4, "desc": "Pulmones verdes"},
    "infraestructura_deportiva": {"meta": 3, "desc": "Canchas/Gimnasios"},
    "estadios": {"meta": 1, "desc": "Eventos"},
    "malls": {"meta": 1, "desc": "Shopping/Ocio"},
    "bancos": {"meta": 2, "desc": "Trámites"},
    "iglesias": {"meta": 2, "desc": "Culto"},
    "museos": {"meta": 1, "desc": "Cultura"},
}

PERFILES_USUARIO = {
    "estudiante": {
        "pesos": {
            "educacion_superior": 5,
            "paradas_metro_tren": 5,
            "paradas_micro": 4,
            "bancos": 3,
            "malls": 3,
            "infraestructura_deportiva": 3,
            "areas_verdes": 2,
            "bencineras": 1,
        },
        "desc": "Prioriza conectividad y educación superior",
    },
    "adulto_mayor": {
        "pesos": {
            "salud": 5,
            "farmacias": 5,
            "paradas_micro": 4,
            "areas_verdes": 4,
            "cuarteles_carabineros": 3,
            "bancos": 3,
            "ferias_libres": 3,
            "educacion_escolar": 1,
            "educacion_superior": 1,
            "infraestructura_deportiva": 1,
        },
        "desc": "Prioriza salud, tranquilidad y abasto local",
    },
    "familia_joven": {
        "pesos": {
            "educacion_escolar": 5,
            "areas_verdes": 5,
            "salud": 4,
            "supermercados": 4,
            "cuarteles_carabineros": 4,
            "bencineras": 3,
            "malls": 3,
            "educacion_superior": 1,
        },
        "desc": "Prioriza colegios, parques y seguridad",
    },
}


# ============================================================================
# FUNCIONES DE CARGA Y LOGICA
# ============================================================================


@st.cache_resource
def cargar_servicios_unificados(gpkg_path, _mtime=None):
    """
    Carga todas las capas, las etiqueta y las une en un solo GeoDataFrame.
    Usa caché de recurso de Streamlit para no recargar ni serializar en cada interacción.
    El parámetro _mtime se usa para invalidar el caché si el archivo cambia.
    """
    lista_gdfs = []

    # Iteramos sobre las capas definidas
    for category, layer_name in SERVICE_LAYERS.items():
        try:
            # Cargamos la capa individual
            gdf = gpd.read_file(gpkg_path, layer=layer_name)

            # Mantenemos solo geometry y agregamos categoría
            if not gdf.empty:
                gdf = gdf[["geometry"]].copy()
                gdf["tipo_servicio"] = category
                lista_gdfs.append(gdf)
        except Exception as e:
            # Podríamos loguear el error, pero continuamos con lo que haya
            pass

    if not lista_gdfs:
        return gpd.GeoDataFrame(columns=["geometry", "tipo_servicio"], crs="EPSG:32719")

    # Unimos todo
    gdf_total = pd.concat(lista_gdfs, ignore_index=True)

    # Aseguramos CRS métrico (EPSG:32719 para Santiago/Chile)
    if gdf_total.crs is None or gdf_total.crs.to_string() != "EPSG:32719":
        gdf_total = gdf_total.to_crs(epsg=32719)

    return gdf_total


@st.cache_data(show_spinner=False)
def obtener_servicios_en_radio(_gdf_servicios, lat, lon, radio_metros=1000):
    """
    Cuenta cuántos servicios de cada tipo hay alrededor de (lat, lon).
    """
    # 1. Crear punto usuario (WGS84 -> EPSG:32719)
    punto_usuario = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)], crs="EPSG:4326"
    ).to_crs(_gdf_servicios.crs)

    # 2. Crear buffer
    circulo = punto_usuario.buffer(radio_metros).iloc[0]

    # 3. Filtrar espacialmente
    servicios_cercanos = _gdf_servicios[_gdf_servicios.intersects(circulo)]

    # 4. Contar
    conteo = servicios_cercanos["tipo_servicio"].value_counts().to_dict()

    # Rellenar ceros
    for servicio in SERVICE_LAYERS.keys():
        if servicio not in conteo:
            conteo[servicio] = 0

    return conteo


def obtener_geometrias_servicios_en_radio(gdf_servicios, lat, lon, radio_metros=1000):
    """
    Retorna las geometrías de servicios encontrados alrededor de (lat, lon).
    Útil para visualizar los puntos en el mapa.
    """
    # 1. Crear punto usuario (WGS84 -> EPSG:32719)
    punto_usuario = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)], crs="EPSG:4326"
    ).to_crs(gdf_servicios.crs)

    # 2. Crear buffer
    circulo = punto_usuario.buffer(radio_metros).iloc[0]

    # 3. Filtrar espacialmente
    servicios_cercanos = gdf_servicios[gdf_servicios.intersects(circulo)]

    # 4. Convertir a WGS84 para Folium (que usa coordenadas geográficas)
    if not servicios_cercanos.empty:
        servicios_cercanos = servicios_cercanos.to_crs("EPSG:4326")

    return servicios_cercanos


@st.cache_data(show_spinner=False)
def obtener_servicios_mas_cercanos(
    _gdf_servicios, lat, lon, tipos_faltantes, radio_metros=1000
):
    """
    Para cada tipo de servicio faltante, encuentra el servicio más cercano fuera del radio.
    Retorna un diccionario con {tipo_servicio: (distancia_m, geometria_wgs84, fila_completa)}
    """
    # 1. Crear punto usuario
    punto_usuario = gpd.GeoDataFrame(
        geometry=[Point(lon, lat)], crs="EPSG:4326"
    ).to_crs(_gdf_servicios.crs)

    # 2. Crear buffer
    circulo = punto_usuario.buffer(radio_metros).iloc[0]

    # 3. Servicios fuera del radio
    servicios_fuera_radio = _gdf_servicios[~_gdf_servicios.intersects(circulo)]

    resultados = {}

    for tipo in tipos_faltantes:
        # Filtrar por tipo
        servicios_tipo = servicios_fuera_radio[
            servicios_fuera_radio["tipo_servicio"] == tipo
        ]

        if not servicios_tipo.empty:
            # Calcular distancias desde cada servicio hasta el punto usuario
            punto_geom = punto_usuario.iloc[0].geometry
            distancias = servicios_tipo.geometry.distance(punto_geom)

            # Encontrar el más cercano
            idx_min = distancias.idxmin()
            distancia_min = distancias.min()
            servicio_mas_cercano = servicios_tipo.loc[idx_min]

            # Convertir geometría a WGS84
            geom_wgs84 = servicio_mas_cercano.geometry
            if _gdf_servicios.crs != "EPSG:4326":
                punto_wgs84 = (
                    gpd.GeoDataFrame(geometry=[geom_wgs84], crs=_gdf_servicios.crs)
                    .to_crs("EPSG:4326")
                    .iloc[0]
                    .geometry
                )
            else:
                punto_wgs84 = geom_wgs84

            resultados[tipo] = {
                "distancia_m": distancia_min,
                "geometria": punto_wgs84,
                "servicio": servicio_mas_cercano,
            }

    return resultados


def calcular_distancia_minima_por_categoria(gdf_origen, gdf_servicios):
    """
    Para cada punto en gdf_origen, calcula la distancia al servicio más cercano de cada tipo.
    gdf_origen: GeoDataFrame con puntos.
    gdf_servicios: GeoDataFrame unificado con columna 'tipo_servicio'.
    """
    res_df = gdf_origen.copy()

    for tipo in gdf_servicios["tipo_servicio"].unique():
        servicios_tipo = gdf_servicios[gdf_servicios["tipo_servicio"] == tipo]
        if not servicios_tipo.empty:
            # Usar sindex para velocidad
            # Para cada punto de origen, encontrar la distancia al más cercano
            distancias = []
            for geom in gdf_origen.geometry:
                d = servicios_tipo.distance(geom).min()
                distancias.append(d)
            res_df[f"dist_min_{tipo}"] = distancias

    return res_df


def normalizar_conteo(servicio_key, conteo_real):
    """
    Normaliza el conteo a puntaje 0.0 - 1.0 según SCORING_CONFIG.
    """
    meta = 1
    if servicio_key in SCORING_CONFIG:
        meta = SCORING_CONFIG[servicio_key]["meta"]

    score = min(conteo_real / meta, 1.0)
    return score


def calcular_indice_calidad_vida(gdf_servicios, lat, lon, perfil_key):
    """
    Calcula el índice final para un perfil dado en una ubicación.
    """
    if perfil_key not in PERFILES_USUARIO:
        return {"error": f"Perfil '{perfil_key}' no encontrado."}

    pesos_perfil = PERFILES_USUARIO[perfil_key]["pesos"]

    # 1. Obtener datos
    conteo_servicios = obtener_servicios_en_radio(
        gdf_servicios, lat, lon, radio_metros=1000
    )

    puntaje_total_ponderado = 0
    suma_pesos_maximos = 0
    detalles = {}

    # 2. Calcular
    for servicio, conteo in conteo_servicios.items():
        puntaje_norm = normalizar_conteo(servicio, conteo)
        peso = pesos_perfil.get(servicio, 1)

        aporte = puntaje_norm * peso
        puntaje_total_ponderado += aporte
        suma_pesos_maximos += peso

        # Include all services in details, even with zero contributions
        detalles[servicio] = {
            "conteo": conteo,
            "score_norm": round(puntaje_norm, 2),
            "importancia": peso,
            "aporte_final": round(aporte, 2),
        }

    # 3. Final
    if suma_pesos_maximos == 0:
        indice_final = 0
    else:
        indice_final = (puntaje_total_ponderado / suma_pesos_maximos) * 100

    return {
        "indice": round(indice_final, 1),
        "perfil": perfil_key,
        "lat": lat,
        "lon": lon,
        "detalles": detalles,
    }
