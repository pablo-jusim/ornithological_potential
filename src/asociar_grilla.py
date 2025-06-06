# Potencial Ornitológico Fueguino
# Autor: Pablo Jusim

# Este script va a asociar cada fila de datos de obsevaciones
# a la grilla correspondiente.
# Input: Archivos csv que tengan columnas que comiencen con
# "latitud" y "longitud" sin distinguir mayúsculas de minúsculas
# Output: archivo csv con la columna extra "celda"

# %% Importaciones
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# %% Detectar columnas lat y long

def detect_lat_lon_columns(df):
    """
    Detecta columnas de latitud y longitud en un DataFrame.
    Busca nombres de columnas que comiencen con lat_prefix o lon_prefix
    (sin distinguir mayúsculas).

    Args:
        df: DataFrame de pandas con las columnas a inspeccionar.
    Returns:
        Tupla conteniendo los nombres de columnas para latitud y longitud
    Raises:
        ValueError: si no encuentra exactamente una columna para cada
                    coordenada.
    """
    lat_prefix = 'latitud'
    lon_prefix = 'longitud'

    cols = df.columns
    lat_cols = [c for c in cols if c.lower().startswith(lat_prefix.lower())]
    lon_cols = [c for c in cols if c.lower().startswith(lon_prefix.lower())]

    if len(lat_cols) != 1:
        raise ValueError(f"""Se esperaba exactamente 1 columna de latitud que
                          comience con '{lat_prefix}', pero se encontraron:
                          {lat_cols}""")
    if len(lon_cols) != 1:
        raise ValueError(f"""Se esperaba exactamente 1 columna de longitud que
                          comience con '{lon_prefix}', pero se encontraron:
                          {lon_cols}""")

    return lat_cols[0], lon_cols[0]

# %% Asignar celda a la fila


def assign_grid_cell_ids(
    grilla: str,
    datos_georef: str,
    grid_id_field: str = 'cell_id',
    grid_layer: str = None,
    geoide: int = 4326
):
    """
    Lee una grilla de celdas desde un archivo .gpkg, carga un CSV de puntos,
    detecta las columnas de latitud y longitud, y asigna a cada punto el ID de
    la celda de la grilla en la que cae. Guarda el resultado en un nuevo CSV.

    :param grilla: Ruta al archivo .gpkg con la grilla de celdas.
    :param df_points: Ruta al archivo CSV con los puntos
      (columnas lat/lon detectadas).
    :param grid_id_field: Nombre del campo que contiene el ID en la grilla.
    :param grid_layer: Nombre de la capa dentro del .gpkg. Si es None,
     usa la capa por defecto.
    :param geoide: Geoide usado para proyectar la capa de puntos
    """
    # Cargar la grilla
    gdf_grid = gpd.read_file(grilla, layer=grid_layer)

    if grid_id_field not in gdf_grid.columns:
        raise KeyError(f"El campo '{grid_id_field}' no existe en la grilla.")

    if isinstance(datos_georef, str):  # si es una ruta
        df_points = pd.read_csv(datos_georef)
    elif isinstance(datos_georef, pd.DataFrame):  # si ya es un DataFrame
        df_points = datos_georef.copy()
    else:
        raise TypeError("`datos_georef` debe ser una ruta a un CSV o un"
                        "DataFrame de pandas.")

    # Detectar columnas de latitud y longitud
    lat_col = next((c for c in df_points.columns if c.lower().
                    startswith('latitud')), None)
    lon_col = next((c for c in df_points.columns if c.lower().
                    startswith('longitud')), None)

    # Crear GeoDataFrame de puntos
    gdf_pts = gpd.GeoDataFrame(
        df_points,
        geometry=[Point(xy) for xy in zip(df_points[lon_col],
                                          df_points[lat_col])],
        crs=f'EPSG:{geoide}'
    )

    # Reproyectar si es necesario
    if gdf_pts.crs != gdf_grid.crs:
        gdf_pts = gdf_pts.to_crs(gdf_grid.crs)

    # Spatial join para asignar ID de celda
    gdf_joined = gpd.sjoin(
        gdf_pts,
        gdf_grid[[grid_id_field, 'geometry']],
        how='left',
        predicate='within'
    )

    # Convertir el ID de celda a entero (manteniendo NaNs si los hay)
    gdf_joined[grid_id_field] = gdf_joined[grid_id_field].astype('Int64')
    # Filtrar solo los puntos que tienen celda asignada
    gdf_joined = gdf_joined[gdf_joined[grid_id_field].notna()].copy()
    # Eliminar la columna de geometría y la del índice del join ('index_right')
    df_resultado = gdf_joined.drop(columns=['geometry', 'index_right'])

    # Devolver el resultado
    return df_resultado
