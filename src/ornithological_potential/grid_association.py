"""
Point-to-grid association script

This script loads a grid GeoPackage and a set of observations,
associates each point to its containing grid cell via a spatial join, and
returns a DataFrame with an extra `cell_id` column.

Steps:
1. Detect latitude/longitude columns in the observations.
2. Load grid cells from GeoPackage.
3. Build a GeoDataFrame of points.
4. Spatially join points to grid cells.
5. Return only points that fall within a cell.

Designed to be imported by other scripts; no file I/O is performed.
"""

# %% Imports
import sys
import logging
from pathlib import Path
from typing import Union

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_lat_lon_columns(
        df: pd.DataFrame,
        lat_prefix: str = 'latitude',
        lon_prefix: str = 'longitude'
) -> tuple:
    """
    Detect latitude and longitude columns in a DataFrame.

    Args:
        df (pd.DataFrame): Input pandas DataFrame.
        lat_prefix (str): Case-insensitive prefix for latitude.
        lon_prefix (str): Case-insensitive prefix for longitude.

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


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------

def assign_grid_cell_ids(
    grid_file: Union[str, Path],
    observations: Union[str, pd.DataFrame],
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
        (default: 'cell_id').
        grid_layer (str): Layer name within the GeoPackage
        (default: first layer).
        epsg_code (int): EPSG code for the CRS of the observation points.
        (default: 4326).

    Returns:
        pd.DataFrame: Original observations with an extra column
        for the assigned cell ID.
    """
    # 1. Load the grid
    grid_path = Path(grid_file)
    gdf_grid = gpd.read_file(grid_path, layer=grid_layer)
    if cell_id_field not in gdf_grid.columns:
        raise KeyError(f"Field '{cell_id_field}' not found in grid cells.")

    # 2. Load observations
    if isinstance(observations, str):
        df_obs = pd.read_csv(observations)
    elif isinstance(observations, pd.DataFrame):
        df_obs = observations.copy()
    else:
        raise TypeError(
            "`observations` must be a pandas DataFrame or a path to"
            "a CSV file."
        )

    # 3. Detect lat/lon and build points GeoDataFrame
    lat_col, lon_col = detect_lat_lon_columns(df_obs)
    gdf_pts = gpd.GeoDataFrame(
        df_obs,
        geometry=[Point(xy) for xy in zip(df_obs[lon_col], df_obs[lat_col])],
        crs=f"EPSG:{epsg_code}"
    )

    # 4. Reproject if needed
    if gdf_pts.crs != gdf_grid.crs:
        gdf_pts = gdf_pts.to_crs(gdf_grid.crs)

    # 5. Spatial join
    gdf_joined = gpd.sjoin(
        gdf_pts,
        gdf_grid[[cell_id_field, 'geometry']],
        how='left',
        predicate='within'
    )

    # 6. Clean up and return
    gdf_joined[cell_id_field] = gdf_joined[cell_id_field].astype('Int64')
    result = (
        gdf_joined[gdf_joined[cell_id_field].notna()]
        .drop(columns=['geometry', 'index_right'])
    )
    logging.info("Assigned %d points to cells", len(result))
    return pd.DataFrame(result)


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------

def main(
    grid_file: Union[str, Path],
    observations: Union[str, pd.DataFrame],
    cell_id_field: str = 'grid_id',
    grid_layer: str = None,
    epsg_code: int = 4326
) -> pd.DataFrame:
    """
    Execute the assignment and save the result.

    Args:
        grid_file: Path to the grid GeoPackage.
        observations: CSV path or DataFrame of points.
        cell_id_field: Grid ID column name.
        grid_layer: GeoPackage layer name.
        epsg_code: CRS code for input points.

    Returns:
        The DataFrame of observations with assigned `cell_id`.
    """

    df_assoc = assign_grid_cell_ids(
        grid_file=grid_file,
        observations=observations,
        cell_id_field=cell_id_field,
        grid_layer=grid_layer,
        epsg_code=epsg_code
    )

    return df_assoc
