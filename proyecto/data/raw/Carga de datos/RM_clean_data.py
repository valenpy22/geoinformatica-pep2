import pandas as pd
import os

# --- 1. CONSTANTES ---
# Definir todas tus variables al principio
ARCHIVO_EXCEL = 'D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx'
NOMBRE_HOJA = '4'
ARCHIVO_SALIDA_CSV = 'censo_RM_totales_comuna.csv'

COLUMNAS_CORRECTAS = [
    'Código región', 'Región', 'Código provincia', 'Provincia',
    'Código comuna', 'Comuna', 'Grupos de edad', 'Población censada',
    'Hombres', 'Mujeres', 'Razón hombre-mujer'
]
COLUMNAS_UTILES = [
    'Código comuna', 'Comuna', 'Población censada', 'Hombres', 'Mujeres'
]
COLUMNAS_A_INT = {
    'Población censada': int,
    'Hombres': int,
    'Mujeres': int
}

# --- 2. FUNCIÓN PRINCIPAL DEL SCRIPT ---
def limpiar_censo():
    """
    Proceso ETL para limpiar el archivo Excel del Censo,
    filtrar por la RM y guardar los totales por comuna en un CSV.
    """

    print("\n" + "="*50)
    print("     INICIANDO PASO 1: Limpieza de datos del Censo")
    print("="*50)

    # --- 1. EXTRACCIÓN ---
    print(f"Cargando archivo: {ARCHIVO_EXCEL}, Hoja: '{NOMBRE_HOJA}'...")
    try:
        df_censo_raw = pd.read_excel(
            ARCHIVO_EXCEL,
            sheet_name=NOMBRE_HOJA,
            skiprows=4,
            header=None,
            names=COLUMNAS_CORRECTAS
        )
    except FileNotFoundError:
        print(f"¡Error! No se encontró el archivo '{ARCHIVO_EXCEL}'.")
        print("Asegúrate de tener 'openpyxl' (pip install openpyxl).")
        return # Sale de la función si hay error
    except Exception as e:
        print(f"¡Error al leer el archivo Excel! {e}")
        return

    print("Archivo cargado con los nombres de columna correctos.")

    # --- 2. TRANSFORMACIÓN ---

    # 2.1. Filtrar por RM
    df_rm = df_censo_raw[df_censo_raw['Código región'] == 13].copy()

    # 2.2. Filtrar por 'Total Comuna'
    df_rm_totales = df_rm[df_rm['Grupos de edad'] == 'Total Comuna'].copy()

    # 2.3. Seleccionar solo columnas útiles
    # ¡Agregamos .copy() para evitar cualquier advertencia!
    df_rm_limpio = df_rm_totales[COLUMNAS_UTILES].copy()

    print("\nConvirtiendo columnas de población a tipo 'int' (entero)...")
    try:
        # 2.4. Convertir tipos de dato (llaves y población)
        df_rm_limpio['Código comuna'] = df_rm_limpio['Código comuna'].astype(int)

        # ¡MEJORA! Convertimos las 3 columnas de una vez
        df_rm_limpio = df_rm_limpio.astype(COLUMNAS_A_INT)

        print("¡Conversión exitosa!")
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo convertir a 'int'. Error: {e}")
        return

    print(f"\n¡Se encontraron y procesaron {len(df_rm_limpio)} comunas en total!")
    print(df_rm_limpio)

    # --- 3. CARGA ---
    df_rm_limpio.to_csv(ARCHIVO_SALIDA_CSV, index=False)
    print(f"\n¡Éxito! Datos de totales guardados en: {ARCHIVO_SALIDA_CSV}")

    # --- 4. CÁLCULO TOTAL ---
    print("\n" + "="*50)
    print("     CÁLCULO TOTAL REGIÓN METROPOLITANA (Censo)")
    print("="*50)

    total_poblacion_rm = df_rm_limpio['Población censada'].sum()
    print(f"La población total censada en la Región Metropolitana es: {total_poblacion_rm:,.0f} habitantes.")
    print("="*50)


# --- 4. EJECUCIÓN DEL SCRIPT ---
# Esta es la forma estándar de ejecutar un script de Python
if __name__ == "__main__":
    limpiar_censo()
