# Potencial Ornitológico Fueguino
# Autor: Pablo Jusim

# Creación de la grilla de mapa
# El objetivo de este script es crear una grilla sobre el mapa del
# sector argentino de la Isla Grande de Tierra del Fuego.
# Cada celda de la grilla medirá 5 km de lado y tendrá un valor de id.

# %% Importaciones
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import box
import pandas as pd
import numpy as np


# %% Carga de mapa base de contorno

# Ubicación del archivo de referencia para limitar el área de la grilla
archivo = '../../data/raw/contorno_tdf.gpkg'

# 1.1 Cargar la extensión de Tierra del Fuego desde un GeoPackage
tf = gpd.read_file(archivo).to_crs(epsg=4326)


# %% Calcular el tamaño de la celda en grados
# Para que tenga 5.000 m de lado

# Obtener el punto de inicio, al extremo suroeste de TDF
    # Extraer los límites: xmin, ymin, xmax, ymax
xmin, ymin, xmax, ymax = tf.total_bounds
    # Crear el punto suroeste
southwest = Point(xmin, ymin)

# %% Hacer un df de grilla con los puntos extremos sudoeste de cada celda
# Se considera que 5 km de lado en -54° latitud y -68° longitud
# corresponden a cambio_latitud ≈ 0.0449° y cambio_longitud ≈ 0.0783°

# Calcular el tamaño de la celda en grados
LAT_STEP = 5 / 111.32
LON_STEP = LAT_STEP / np.cos(np.deg2rad(55))

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
        lon0 += LON_STEP
    lat0 += LAT_STEP

grid_df = pd.DataFrame(grid_rows, columns=["grid_id", "lat", "lon"])

# %% Filtrar la grilla para solo incluir celdas dentro de TDF

# Convertir el DataFrame a GeoDataFrame
grid_gdf = gpd.GeoDataFrame(
    grid_df,
    geometry=grid_df.apply(
        lambda r: box(
            r.lon,
            r.lat,
            r.lon + LON_STEP,
            r.lat + LAT_STEP
        ),
        axis=1
    ),
    crs="EPSG:4326"
)

# Filtrar las celdas que están dentro del polígono de TDF
tf_union = tf.union_all()
grid_clipped = grid_gdf[grid_gdf.geometry.intersects(tf_union)].copy()

# Reasignar los ids de las celdas
grid_clipped.reset_index(drop=True, inplace=True)

# %% Exportar la grilla a un archivo GeoPackage
output_file = '../../data/interim/grilla_tdf_vacia.gpkg'
grid_clipped.to_file(output_file, driver='GPKG', layer='grilla_tdf_vacia')
