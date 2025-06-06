# Potencial Ornitológico Fueguino
# Autor: Pablo Jusim

# Creación de la grilla de mapa
# El objetivo de este script es crear una grilla sobre el mapa del
# sector argentino de la Isla Grande de Tierra del Fuego.
# Cada celda de la grilla medirá 5 km de lado y tendrá un valor de id.

# %% Importaciones
import geopandas as gpd
from shapely.geometry import box
import pandas as pd
import numpy as np


# %% Carga de mapa base de contorno

# 1.1 Cargar la extensión de Tierra del Fuego desde un GeoPackage
def cargar_geopackage(archivo, geoide):
    """
    Carga un archivo GeoPackage y devuelve un GeoDataFrame.

    Args:
        archivo (str): Ruta al archivo GeoPackage
        geoide (str): Sistema de referencia de coordenadas (CRS) usado
    Returns:
        GeoDataFrame: GeoDataFrame abierto
    """
    return gpd.read_file(archivo).to_crs(epsg=geoide)

# %% Calcular el tamaño de la celda en grados
# Para que tenga 5.000 m de lado


# Obtener el punto de inicio, al extremo suroeste de TDF
def obtener_extremos(geo_df):
    """Obtiene el punto suroeste del GeoDataFrame.
    Args:
        geo_df (GeoDataFrame): GeoDataFrame con geometrías.
    Returns:
        Tupla contentiendo los puntos sudeste (xmin, ymin)
        y noreste (xmax, ymax).
    """
    xmin, ymin, xmax, ymax = geo_df.total_bounds
    return xmin, ymin, xmax, ymax

# %% Hacer un df de grilla con los puntos extremos sudoeste de cada celda
# Se considera que 5 km de lado en -54° latitud y -68° longitud
# corresponden a cambio_latitud ≈ 0.0449° y cambio_longitud ≈ 0.0783°


def calcular_tamano_celda(contorno, lado_celda):
    """
    Calcula el tamaño de la celda en grados para una grilla.
    Args:
        contorno (GeoDataFrame): GeoDataFrame con el contorno del área.
        lado_celda (float): Lado de la celda en kilómetros.
    Returns:
        tuple: Tamaño de la celda en grados (lat_step, lon_step).
    """
    # Calcular el tamaño de la celda en grados
    lat_step = lado_celda / 111.32  # Aproximadamente 5 km en grados de latitud
    _, ymin, _, ymax = obtener_extremos(contorno)
    lat_media = (ymin + ymax) / 2

    lon_step = lat_step / np.cos(np.deg2rad(lat_media))  # Ajuste para longitud
    return lat_step, lon_step


def grillar(contorno, lado_celda):
    """
    Crea una grilla de celdas de lado_celda km de lado sobre el contorno dado.
    Args:
        contorno (GeoDataFrame): GeoDataFrame con el contorno del área.
        lado_celda (float): Tamaño del lado de la celda en kilómetros
    Returns:
        GeoDataFrame: GeoDataFrame con la grilla de celdas.
    """
    # Obtener los límites del contorno
    xmin, ymin, xmax, ymax = obtener_extremos(contorno)

    # Calcular el tamaño de la celda en grados
    lat_step, lon_step = calcular_tamano_celda(contorno, lado_celda)

    # Generar la grilla
    grid_rows = []
    cid = 0
    lat0 = ymin
    while lat0 <= ymax:
        lon0 = xmin
        while lon0 <= xmax:
            grid_rows.append({
                "grid_id": cid,
                "lat": round(lat0, 6),
                "lon": round(lon0, 6)
            })
            cid += 1
            lon0 += lon_step
        lat0 += lat_step

    return pd.DataFrame(grid_rows, columns=["grid_id", "lat", "lon"])

# %% Filtrar la grilla para solo incluir celdas dentro de TDF


# Convertir el DataFrame a GeoDataFrame
def df_a_geodf(df, geoide, contorno, lado_celda):
    """
    Convierte un DataFrame a GeoDataFrame con geometría de puntos.
    Args:
        df (DataFrame): DataFrame con columnas 'lat' y 'lon'.
        geoide (int): EPSG code para el sistema de referencia.
    Returns:
        GeoDataFrame: GeoDataFrame con geometría de puntos.
    """
    lat_step, lon_step = calcular_tamano_celda(contorno, lado_celda)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=df.apply(
            lambda r: box(
                r.lon,
                r.lat,
                r.lon + lon_step,
                r.lat + lat_step
            ),
            axis=1
        ),
        crs=f"EPSG:{geoide}"
    )
    return gdf


# Filtrar las celdas que están dentro del polígono de TDF
def filtrar_en_contorno(gdf, contorno):
    """
    Filtra un GeoDataFrame para incluir solo las geometrías que intersectan con el contorno dado.
    Args:
        gdf (GeoDataFrame): GeoDataFrame con geometrías a filtrar.
        contorno (GeoDataFrame): GeoDataFrame con el contorno del área.
    Returns:
        GeoDataFrame: GeoDataFrame filtrado.
    """
    cont_union = contorno.union_all()
    geodf = gdf[gdf.geometry.intersects(cont_union)].copy()
    geodf.reset_index(drop=True, inplace=True)
    return geodf

# %% Funcion principal para ejecutar el script


def main(archivo_cont, geoide=4326, lado_celda=5):
    """
    Función principal para ejecutar el script de creación de grilla.
    """
    contorno = cargar_geopackage(archivo_cont, geoide)
    grilla_base = grillar(contorno, lado_celda)
    geo_df = df_a_geodf(grilla_base, geoide, contorno, lado_celda)
    geo_df_filtrado = filtrar_en_contorno(geo_df, contorno)
    return geo_df_filtrado

 
