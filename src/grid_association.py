# Ornithological Potential
# Author: Pablo Jusim

# Point-to-grid association script
# This script associates each observation record with its corresponding
# grid cell.
# Input: CSV files containing columns starting with "latitude" and "longitude"
# (case-insensitive).
# Output: A DataFrame with an extra column "cell_id" indicating the assigned
# grid cell.

# %% Imports
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# %% Detect latitude and longitude columns

def detect_lat_lon_columns(df: pd.DataFrame, lat_prefix: str = 'latitude',
                           lon_prefix: str = 'longitude') -> tuple:
    """
    Detect latitude and longitude columns in a DataFrame.
    Searches for column names starting with given prefixes (case-insensitive).

    Args:
        df (DataFrame): Input pandas DataFrame.
        lat_prefix (str): Prefix for latitude column names.
        Default: 'latitude'.
        lon_prefix (str): Prefix for longitude column names.
        Default: 'longitude'.

    Returns:
        tuple: (latitude_column_name, longitude_column_name).

    Raises:
        ValueError: If exactly one latitude or longitude column is not found.
    """
    cols = df.columns
    lat_cols = [c for c in cols if c.lower().startswith(lat_prefix.lower())]
    lon_cols = [c for c in cols if c.lower().startswith(lon_prefix.lower())]

    if len(lat_cols) != 1:
        raise ValueError(
            f"""Expected exactly one latitude column starting with
            '{lat_prefix}', found: {lat_cols}"""
        )
    if len(lon_cols) != 1:
        raise ValueError(
            f"""Expected exactly one longitude column starting with
            '{lon_prefix}', found: {lon_cols}"""
        )

    return lat_cols[0], lon_cols[0]

# %% Associate observations to grid cells


def assign_grid_cell_ids(
    grid_file: str,
    observations: pd.DataFrame | str,
    cell_id_field: str = 'cell_id',
    grid_layer: str = None,
    epsg_code: int = 4326
) -> pd.DataFrame:
    """
    Assign each observation record to a grid cell based on spatial join.

    Args:
        grid_file (str): Path to the GeoPackage file containing the grid cells.
        observations (DataFrame or str): pandas DataFrame or path to a CSV file
            with observation points (latitude/longitude columns
            detected automatically).
        cell_id_field (str): Name of the grid cell ID column in the grid.
        Default: 'cell_id'.
        grid_layer (str): Layer name within the GeoPackage. If None,
        defaults to the first layer.
        epsg_code (int): EPSG code for the CRS of the observation points.
        Default: 4326.

    Returns:
        DataFrame: Original observations with an extra column for the assigned
        cell ID.
    """
    # Load grid GeoDataFrame
    gdf_grid = gpd.read_file(grid_file, layer=grid_layer)

    if cell_id_field not in gdf_grid.columns:
        raise KeyError(f"Field '{cell_id_field}' not found in grid cells.")

    # Load observations DataFrame
    if isinstance(observations, str):
        df_obs = pd.read_csv(observations)
    elif isinstance(observations, pd.DataFrame):
        df_obs = observations.copy()
    else:
        raise TypeError(
            "`observations` must be a pandas DataFrame or a path to"
            "a CSV file."
        )

    # Detect lat/lon columns
    lat_col, lon_col = detect_lat_lon_columns(df_obs)

    # Convert to GeoDataFrame of points
    gdf_pts = gpd.GeoDataFrame(
        df_obs,
        geometry=[Point(xy) for xy in zip(df_obs[lon_col], df_obs[lat_col])],
        crs=f"EPSG:{epsg_code}"
    )

    # Reproject points to match grid CRS if necessary
    if gdf_pts.crs != gdf_grid.crs:
        gdf_pts = gdf_pts.to_crs(gdf_grid.crs)

    # Spatial join: assign cell IDs
    gdf_joined = gpd.sjoin(
        gdf_pts,
        gdf_grid[[cell_id_field, 'geometry']],
        how='left',
        predicate='within'
    )

    # Convert cell ID to nullable integer type
    gdf_joined[cell_id_field] = gdf_joined[cell_id_field].astype('Int64')

    # Keep only points with assigned cell
    df_result = (
        gdf_joined[gdf_joined[cell_id_field].notna()]
        .drop(columns=['geometry', 'index_right'])
    )

    return df_result
