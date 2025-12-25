import pandas as pd
import geopandas as gpd
import os

# --- 1. CONSTANTES GLOBALES ---
CRS_PROYECTO = "EPSG:32719"
RUTA_GPKG = 'geodatabase_proyecto.gpkg'
CAPA_COMUNAS_RM = 'comunas_rm_censo'

# --- 2. CREACIÓN DE LA CAPA BASE (COMUNAS + CENSO) ---
print("\n" + "="*50)
print(f"     INICIANDO PROCESO: Capa Base '{CAPA_COMUNAS_RM}'")
print("="*50)

# 2.1. Cargar DPA (Mapa)
ruta_shapefile = 'DPA_2023/COMUNAS/COMUNAS_v1.shp'
print(f"Cargando mapa de comunas de Chile: {ruta_shapefile}...")
try:
    gdf_chile_completo = gpd.read_file(ruta_shapefile)
except Exception as e:
    print(f"¡Error! No se pudo leer el Shapefile. {e}")
    exit()

# 2.2. Cargar Censo (CSV)
ruta_censo_csv = 'censo_RM_totales_comuna.csv'
print(f"Cargando datos del Censo: {ruta_censo_csv}...")
df_censo = pd.read_csv(ruta_censo_csv)

# 2.3. Filtrar DPA por RM
print("Filtrando mapa por Región Metropolitana (Código '13')...")
gdf_rm = gdf_chile_completo[gdf_chile_completo['CUT_REG'] == '13'].copy()

# 2.4. Normalizar llaves
try:
    gdf_rm['CUT_COM'] = gdf_rm['CUT_COM'].astype(int)
    df_censo['Código comuna'] = df_censo['Código comuna'].astype(int)
except Exception as e:
    print(f"Error normalizando las llaves: {e}")
    exit()

# 2.5. Unir (Merge)
print("Uniendo datos del Censo al mapa de la RM...")
gdf_rm_con_censo = gdf_rm.merge(
    df_censo, 
    left_on='CUT_COM',
    right_on='Código comuna'
)

# 2.6. Limpiar columna duplicada
if 'Comuna' in gdf_rm_con_censo.columns:
    gdf_rm_con_censo = gdf_rm_con_censo.drop(columns=['Comuna'])

# 2.7. Proyectar a CRS del Proyecto
gdf_rm_con_censo = gdf_rm_con_censo.to_crs(CRS_PROYECTO)

# 2.8. CARGA
print(f"\nGuardando la capa base '{CAPA_COMUNAS_RM}' en {RUTA_GPKG}...")
gdf_rm_con_censo.to_file(
    RUTA_GPKG,
    layer=CAPA_COMUNAS_RM,
    driver='GPKG'
)
print(f"¡ÉXITO! Se creó/actualizó la capa base.")
print("="*50)

def procesar_capa_servicio(ruta_carpeta, 
                           nombre_shp, 
                           nombre_capa_salida, 
                           columna_filtro=None, 
                           valor_filtro=None):
    """
    Función ETL para procesar una capa de servicio (Shapefile),
    filtrarla por la RM y agregarla a la Geodatabase principal.
    
    Si 'columna_filtro' y 'valor_filtro' se especifican, filtra por atributo.
    Si se dejan en None, filtra por ubicación espacial (Spatial Join).
    """
    
    print("\n" + "="*50)
    print(f"     INICIANDO PROCESO: {nombre_capa_salida}")
    print("="*50)
    
    # --- 2. EXTRACCIÓN ---
    ruta_shp_completa = os.path.join(ruta_carpeta, nombre_shp)
    print(f"Cargando capa desde: {ruta_shp_completa}...")
    try:
        gdf_chile = gpd.read_file(ruta_shp_completa)
    except Exception as e:
        print(f"¡Error! No se pudo leer el Shapefile. {e}")
        return 
    
    # --- 3. TRANSFORMACIÓN (Filtrado y Proyección) ---
    
    gdf_rm_proyectado = None # Variable para guardar el resultado final

    # MÉTODO A: FILTRAR POR ATRIBUTO (columna y valor)
    if columna_filtro and valor_filtro:
        print(f"Filtrando por atributo: '{columna_filtro}' == '{valor_filtro}'...")
        try:
            if columna_filtro not in gdf_chile.columns:
                raise ValueError(f"La columna '{columna_filtro}' no existe.")
            
            # Revisa si el valor a filtrar debe ser string o int
            if gdf_chile[columna_filtro].dtype == 'object':
                filtro_a_usar = str(valor_filtro)
            else:
                filtro_a_usar = int(valor_filtro)
                
            gdf_rm_filtrado = gdf_chile[
                gdf_chile[columna_filtro] == filtro_a_usar
            ].copy()
            
            if len(gdf_rm_filtrado) == 0:
                print("ADVERTENCIA: Filtro resultó en 0 elementos. Revisa el valor del filtro.")
            
            print(f"CRS original: {gdf_rm_filtrado.crs}")
            gdf_rm_proyectado = gdf_rm_filtrado.to_crs(CRS_PROYECTO)

        except Exception as e:
            print(f"¡Error al filtrar por atributo! Revisa tus columnas y valores.")
            print(f"Columnas disponibles: {gdf_chile.columns.to_list()}")
            print(f"Error: {e}")
            return

    # MÉTODO B: FILTRAR POR UBICACIÓN (Spatial Join)
    else:
        print(f"Filtrando por ubicación espacial (Spatial Join)...")
        try:
            # 1. Cargar el "cortador de galletas" (las comunas)
            gdf_comunas_rm = gpd.read_file(RUTA_GPKG, layer=CAPA_COMUNAS_RM)
            
            # 2. Proyectar AMBAS capas al MISMO CRS antes de unir
            gdf_chile_proyectado = gdf_chile.to_crs(CRS_PROYECTO)
            gdf_comunas_rm = gdf_comunas_rm.to_crs(CRS_PROYECTO) # (Ya debería estar, pero por si acaso)
            
            # 3. Hacer el cruce espacial
            gdf_rm_proyectado = gpd.sjoin(
                gdf_chile_proyectado, # Los puntos (ej. bomberos)
                gdf_comunas_rm,       # Los polígonos (comunas RM)
                how='inner',
                predicate='within'
            )
        except Exception as e:
            print(f"¡Error durante el Spatial Join! {e}")
            print(f"Asegúrate que la capa '{CAPA_COMUNAS_RM}' existe en {RUTA_GPKG}")
            return

    
    print(f"¡Filtrado! Se encontraron {len(gdf_rm_proyectado)} elementos en la RM.")
    print(f"CRS final: {gdf_rm_proyectado.crs} (Debería ser {CRS_PROYECTO})")

    
    # --- 4. CARGA (Guardar en la Geodatabase) ---
    print(f"Guardando capa '{nombre_capa_salida}' en {RUTA_GPKG}...")
    
    try:
        gdf_rm_proyectado.to_file(
            RUTA_GPKG,
            layer=nombre_capa_salida,
            driver='GPKG'
        )
        print(f"¡ÉXITO! Se agregó la capa '{nombre_capa_salida}' a tu Geodatabase.")
        print("="*50)
    
    except Exception as e:
        print(f"¡Error al guardar en el GeoPackage! {e}")
        return

# --- 4. PROCESAR PARADAS GTFS (stops.txt) ---
def procesar_paradas_gtfs_separadas(ruta_txt, 
                                    nombre_capa_micros, 
                                    nombre_capa_metro):
    """
    Función ETL para procesar 'stops.txt' del GTFS,
    separarlo en paradas de Metro/Tren y paradas de Bus,
    y guardarlos como dos capas separadas.
    """
    
    print("\n" + "="*50)
    print(f"     INICIANDO PROCESO: Paradas GTFS (Micros y Metro)")
    print("="*50)
    
    # --- 1. EXTRACCIÓN (Leer el CSV) ---
    print(f"Cargando archivo de paradas: {ruta_txt}...")
    try:
        df_paradas = pd.read_csv(ruta_txt)
    except Exception as e:
        print(f"¡Error! No se pudo leer el archivo '{ruta_txt}'. {e}")
        return

    print(f"Se cargaron {len(df_paradas)} paradas en total.")

    # --- 2. TRANSFORMACIÓN (Convertir a GeoDataFrame) ---
    print("Convirtiendo de CSV a GeoDataFrame...")
    try:
        # 1. Crear la geometría (CRS inicial siempre es 4326 para Lat/Lon)
        gdf_paradas_total = gpd.GeoDataFrame(
            df_paradas, 
            geometry=gpd.points_from_xy(df_paradas.stop_lon, df_paradas.stop_lat),
            crs="EPSG:4326" 
        )
        
        # 2. Separar las capas ANTES de proyectar
        print("Separando en capas de Metro/Tren y Micros...")
        
        # Filtro: 'stop_id' que empieza con 'PT' es Metro/Tren
        filtro_metro = gdf_paradas_total['stop_id'].str.startswith('PT', na=False)
        
        gdf_metro = gdf_paradas_total[filtro_metro].copy()
        gdf_micros = gdf_paradas_total[~filtro_metro].copy() # '~' significa 'NO'
        
        print(f"Se identificaron {len(gdf_metro)} paradas de Metro/Tren.")
        print(f"Se identificaron {len(gdf_micros)} paradas de Micro.")

        # 3. Proyectar ambas capas al CRS de nuestro proyecto
        print(f"Proyectando capas a {CRS_PROYECTO}...")
        gdf_metro_proyectado = gdf_metro.to_crs(CRS_PROYECTO)
        gdf_micros_proyectado = gdf_micros.to_crs(CRS_PROYECTO)

    except Exception as e:
        print(f"¡Error al convertir o separar! {e}")
        print(f"Asegúrate que el .txt tenga 'stop_lon', 'stop_lat' y 'stop_id'.")
        return

    # --- 3. CARGA (Guardar ambas capas) ---
    
    columnas_a_guardar = ['stop_id', 'stop_code', 'stop_name', 'geometry']
    
    # Guardar capa de Metro
    print(f"Guardando capa '{nombre_capa_metro}' en {RUTA_GPKG}...")
    try:
        columnas_finales_metro = [col for col in columnas_a_guardar if col in gdf_metro_proyectado]
        gdf_metro_proyectado[columnas_finales_metro].to_file(
            RUTA_GPKG,
            layer=nombre_capa_metro,
            driver='GPKG'
        )
        print(f"¡ÉxITO! Se agregó la capa '{nombre_capa_metro}'.")
    
    except Exception as e:
        print(f"¡Error al guardar la capa de Metro! {e}")

    # Guardar capa de Micros
    print(f"Guardando capa '{nombre_capa_micros}' en {RUTA_GPKG}...")
    try:
        columnas_finales_micros = [col for col in columnas_a_guardar if col in gdf_micros_proyectado]
        gdf_micros_proyectado[columnas_finales_micros].to_file(
            RUTA_GPKG,
            layer=nombre_capa_micros,
            driver='GPKG'
        )
        print(f"¡ÉXITO! Se agregó la capa '{nombre_capa_micros}'.")
        print("="*50)
    
    except Exception as e:
        print(f"¡Error al guardar la capa de Micros! {e}")

# --- 5. FUNCIÓN: PROCESAR UN GEOJSON INDIVIDUAL DE OSM ---
def procesar_geojson_individual(ruta_geojson, nombre_capa_salida):
    """
    Función ETL para procesar un ÚNICO archivo GeoJSON
    (que ya se asume filtrado) y agregarlo a la Geodatabase.
    
    Su trabajo es Leer, Proyectar, Limpiar columnas y Guardar.
    """
    
    print("\n" + "="*50)
    print(f"     INICIANDO PROCESO: {nombre_capa_salida} (desde GeoJSON)")
    print("="*50)
    
    # --- 1. EXTRACCIÓN (Leer el GeoJSON) ---
    print(f"Cargando archivo: {ruta_geojson}...")
    try:
        gdf = gpd.read_file(ruta_geojson)
        if gdf.empty:
            print(f"ADVERTENCIA: El GeoJSON '{ruta_geojson}' está vacío.")
            # Continuamos para guardar la capa vacía por consistencia
    except Exception as e:
        print(f"¡Error! No se pudo leer el GeoJSON '{ruta_geojson}'. {e}")
        return # Salir de la función

    # --- 2. TRANSFORMACIÓN (Proyección) ---
    print(f"CRS original: {gdf.crs} (Debería ser EPSG:4326)")
    print(f"Proyectando capa a {CRS_PROYECTO}...")
    try:
        gdf_proyectado = gdf.to_crs(CRS_PROYECTO)
    except Exception as e:
        print(f"¡Error al proyectar! {e}")
        return
        
    # --- 3. TRANSFORMACIÓN (Limpieza de Columnas) ---
    
    # Definimos las columnas útiles de OSM que queremos conservar
    columnas_osm_utiles = [
        'osm_id', 'name', 'amenity', 'shop', 'tourism', 
        'building', 'addr:street', 'addr:housenumber', 'geometry'
    ]
    
    # Vemos cuáles de estas columnas SÍ existen en el archivo
    columnas_existentes = [
        col for col in columnas_osm_utiles if col in gdf_proyectado.columns
    ]
    
    # Si 'geometry' no estaba en la lista (raro), la forzamos
    if 'geometry' not in columnas_existentes and 'geometry' in gdf_proyectado.columns:
        columnas_existentes.append('geometry')
        
    gdf_final = None
    
    # Si encontramos columnas útiles, las usamos
    if len(columnas_existentes) > 1: # (más que solo 'geometry')
         print(f"Conservando columnas útiles: {columnas_existentes}")
         gdf_final = gdf_proyectado[columnas_existentes].copy()
    else:
         # Si no, guardamos todo (es mejor que no guardar nada)
         print("No se encontraron columnas de OSM estándar. Guardando todas las columnas.")
         gdf_final = gdf_proyectado

    # --- 4. CARGA (Guardar en la Geodatabase) ---
    print(f"Guardando capa '{nombre_capa_salida}' en {RUTA_GPKG}...")
    try:
        # Usamos gdf_final (que está limpio)
        gdf_final.to_file(
            RUTA_GPKG,
            layer=nombre_capa_salida,
            driver='GPKG'
        )
        print(f"¡ÉXITO! Se agregó la capa '{nombre_capa_salida}' a tu Geodatabase.")
        print("="*50)
    
    except Exception as e:
        print(f"¡Error al guardar en el GeoPackage! {e}")
        return

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    
    # 1. Establecimientos de Salud
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_establecimientos_de_salud_agosto_2025_20251001042636',
        nombre_shp='layer_establecimientos_de_salud_agosto_2025_20251001042636.shp',
        nombre_capa_salida='establecimientos_salud',
        columna_filtro='COD_REG',
        valor_filtro='13'
    )

    # 2. Establecimientos de Educación
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_establecimientos_educacion_escolar_20220309024120',
        nombre_shp='layer_establecimientos_educacion_escolar_20220309024120.shp',
        nombre_capa_salida='establecimientos_educacion',
        columna_filtro='COD_REG_RB',
        valor_filtro='13'
    )
    
    # 3. Cuarteles de Carabineros
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_cuarteles_20220309024623',
        nombre_shp='layer_cuarteles_20220309024623.shp',
        nombre_capa_salida='cuarteles_carabineros',
        columna_filtro='NOMBRE_REG',
        valor_filtro='REGION METROPOLITANA DE SANTIAGO'
    )
    
    # 4. Compañías de Bomberos (¡El caso especial!)
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_companias_de_bomberos_20231110080349',
        nombre_shp='layer_companias_de_bomberos_20231110080349.shp',
        nombre_capa_salida='companias_bomberos'
    )

    # 5. Paradas de Micros y Metro
    procesar_paradas_gtfs_separadas(
        ruta_txt='GTFS_20250927_v3/stops.txt',
        nombre_capa_micros='paradas_micro',
        nombre_capa_metro='paradas_metro_tren'
    )

    # 6. Infraestructura Deportiva
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_infraestructura_deportiva_20230921043832',
        nombre_shp='layer_infraestructura_deportiva_20230921043832.shp', 
        nombre_capa_salida='infraestructura_deportiva',
        columna_filtro='REGION',
        valor_filtro='Metropólitana'        
    )

    # 7. Municipios
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_municipios_20230915121302',
        nombre_shp='layer_municipios_20230915121302.shp',
        nombre_capa_salida='municipios',
        columna_filtro='COD_REG', 
        valor_filtro='13'    
    )

    # 8. Ferias Libres
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_ferias_libres_20230921043202',
        nombre_shp='layer_ferias_libres_20230921043202.shp',
        nombre_capa_salida='ferias_libres',
        columna_filtro='REGION', 
        valor_filtro='RM'        
    )

    # 9. Áreas Verdes
    procesar_capa_servicio(
        ruta_carpeta='Servicios/Politica-de-Areas-Verdes',
        nombre_shp='AV_Política_Regional_RMS.shp', 
        nombre_capa_salida='areas_verdes',
    )

    # 10. Establecimientos de Educación Superior
    procesar_capa_servicio(
        ruta_carpeta='Servicios/layer_establecimientos_de_educacion_superior_20220309024111', 
        nombre_shp='layer_establecimientos_de_educacion_superior_20220309024111.shp', 
        nombre_capa_salida='establecimientos_educacion_superior',
        columna_filtro='COD_REGION', 
        valor_filtro='13'       
    )

    # 11. Iglesias
    procesar_geojson_individual(
        ruta_geojson='Servicios/churches.geojson',
        nombre_capa_salida='osm_iglesias'
    )
    
    # 12. Museos
    procesar_geojson_individual(
        ruta_geojson='Servicios/museums.geojson',
        nombre_capa_salida='osm_museos'
    )

    # 13. Supermercados
    procesar_geojson_individual(
        ruta_geojson='Servicios/supermarkets.geojson',
        nombre_capa_salida='osm_supermercados'
    )
    
    # 14. Almacenes/Bazares
    procesar_geojson_individual(
        ruta_geojson='Servicios/convenience.geojson',
        nombre_capa_salida='osm_almacenes_barrio'
    )

    # 15. Bancos
    procesar_geojson_individual(
        ruta_geojson="Servicios/banks.geojson",
        nombre_capa_salida="osm_bancos"
    )

    # 16. Malls
    procesar_geojson_individual(
        ruta_geojson="Servicios/malls.geojson",
        nombre_capa_salida="osm_malls"
    )

    # 17. Bencineras
    procesar_geojson_individual(
        ruta_geojson="Servicios/fuel.geojson",
        nombre_capa_salida="osm_bencineras"
    )

    # 18. Estadios
    procesar_geojson_individual(
        ruta_geojson="Servicios/stadiums.geojson",
        nombre_capa_salida="osm_estadios"
    )

    print("\n--- ¡Proceso de todos los servicios completado! ---")

