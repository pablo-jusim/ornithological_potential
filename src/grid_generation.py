# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

# Grid generation script
# This script creates a grid inside the selected bounds.
# Each grid cell measures can be set kilometeres on a side and has
# a unique identifier.

# %% Imports
import geopandas as gpd
from shapely.geometry import box
import pandas as pd
import numpy as np


# %% Load base contour from GeoPackage


def load_geopackage(filepath: str, epsg_code: int) -> gpd.GeoDataFrame:
    """
    Load a GeoPackage file and reproject to the specified CRS.

    Args:
        filepath (str): Path to the GeoPackage file.
        epsg_code (int): EPSG code of the target coordinate reference system.

    Returns:
        GeoDataFrame: Loaded and reprojected GeoDataFrame.
    """
    return gpd.read_file(filepath).to_crs(epsg=epsg_code)

# %% Compute cell size in degrees


def get_extents(geo_df: gpd.GeoDataFrame) -> tuple:
    """
    Get the bounding coordinates of a GeoDataFrame.

    Args:
        geo_df (GeoDataFrame): Input GeoDataFrame with geometries.

    Returns:
        tuple: (xmin, ymin, xmax, ymax) bounding box coordinates.
    """
    xmin, ymin, xmax, ymax = geo_df.total_bounds
    return xmin, ymin, xmax, ymax


def calculate_cell_size(contour: gpd.GeoDataFrame, cell_km: float) -> tuple:
    """
    Calculate the grid cell dimensions in degrees for a given side length
    in kilometers.

    Args:
        contour (GeoDataFrame): GeoDataFrame of the study area boundary.
        cell_km (float): Desired cell side length in kilometers.

    Returns:
        tuple: (lat_step, lon_step) cell dimensions in decimal degrees.
    """
    # Approximate degrees per km at mid-latitude
    lat_step = cell_km / 111.32  # degrees per km latitude
    _, ymin, _, ymax = get_extents(contour)
    mid_lat = (ymin + ymax) / 2

    lon_step = lat_step / np.cos(np.deg2rad(mid_lat))
    return lat_step, lon_step

# %% Generate grid points (southwest corner of each cell)


def generate_grid(contour: gpd.GeoDataFrame, cell_km: float) -> pd.DataFrame:
    """
    Create a DataFrame of grid cell origins (southwest corners) covering
    the contour.

    Args:
        contour (GeoDataFrame): Boundary of the study area.
        cell_km (float): Side length of each cell in kilometers.

    Returns:
        DataFrame: Columns [grid_id, lat, lon] for each cell origin.
    """
    xmin, ymin, xmax, ymax = get_extents(contour)
    lat_step, lon_step = calculate_cell_size(contour, cell_km)

    rows = []
    grid_id = 0
    lat = ymin
    while lat <= ymax:
        lon = xmin
        while lon <= xmax:
            rows.append({"grid_id": grid_id, "lat": round(lat, 6),
                         "lon": round(lon, 6)})
            grid_id += 1
            lon += lon_step
        lat += lat_step

    return pd.DataFrame(rows, columns=["grid_id", "lat", "lon"])

# %% Convert DataFrame to GeoDataFrame of polygons


def df_to_geodf(df: pd.DataFrame, epsg_code: int, contour: gpd.GeoDataFrame,
                cell_km: float) -> gpd.GeoDataFrame:
    """
    Convert a DataFrame of cell origins to a GeoDataFrame of square polygons.

    Args:
        df (DataFrame): Contains 'lat' and 'lon' columns for origins.
        epsg_code (int): EPSG code for the CRS.
        contour (GeoDataFrame): Boundary to compute cell size.
        cell_km (float): Side length of cells in kilometers.

    Returns:
        GeoDataFrame: Polygons representing each grid cell.
    """
    lat_step, lon_step = calculate_cell_size(contour, cell_km)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=df.apply(
            lambda r: box(r.lon, r.lat, r.lon + lon_step, r.lat + lat_step),
            axis=1
        ),
        crs=f"EPSG:{epsg_code}"
    )
    return gdf


# %% Filter grid cells inside the contour

def filter_inside_contour(gdf: gpd.GeoDataFrame,
                          contour: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Keep only grid cells that intersect the study area contour.

    Args:
        gdf (GeoDataFrame): Grid cell polygons.
        contour (GeoDataFrame): Study area boundary.

    Returns:
        GeoDataFrame: Filtered grid cells.
    """
    # Union any multipart geometries into a single shape
    unioned = contour.unary_union
    clipped = gdf[gdf.geometry.intersects(unioned)].copy()
    clipped.reset_index(drop=True, inplace=True)
    return clipped

# %% Main function


def main(contour_file: str, epsg_code: int = 4326,
         cell_km: float = 5) -> gpd.GeoDataFrame:
    """
    Generate a spatial grid of square cells over a given boundary.

    Args:
        contour_file (str): Path to the GeoPackage contour file.
        epsg_code (int): EPSG code for desired CRS (default: 4326).
        cell_km (float): Side length of grid cells in kilometers (default: 5).

    Returns:
        GeoDataFrame: Grid cells clipped to the boundary.
    """
    contour = load_geopackage(contour_file, epsg_code)
    df_grid = generate_grid(contour, cell_km)
    gdf_grid = df_to_geodf(df_grid, epsg_code, contour, cell_km)
    filtered = filter_inside_contour(gdf_grid, contour)
    return filtered
