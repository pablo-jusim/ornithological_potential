# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

"""
Generate a spatial grid of square cells over a given boundary.

Steps:
1. Load boundary contour from GeoPackage
2. Compute cell dimensions in degrees
3. Generate grid origin points
4. Convert origins to square polygons
5. Filter cells inside the contour
6. Export the resulting grid to a GeoPackage
"""

# %% Imports
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box
import pandas as pd
import numpy as np
import logging
import sys

# Default output path
OUTPUT_PATH = '../data/raw/grilla_tdf_vacia.gpkg'

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)

# -----------------------------------------------------------------------------
# Step 1: Load boundary contour
# -----------------------------------------------------------------------------
def load_geopackage(
    filepath: Path,
    epsg_code: int
) -> gpd.GeoDataFrame:
    """
    Load a GeoPackage file and reproject to the specified CRS.

    Args:
        filepath (Path): Path to the GeoPackage boundary file.
        epsg_code (int): EPSG code of the target CRS.

    Returns:
        GeoDataFrame: Reprojected boundary GeoDataFrame.
    """
    # Resolve relative path based on script location
    if not filepath.is_absolute():
        root_dir = Path(__file__).resolve().parent
        filepath = root_dir / filepath
    if not filepath.exists():
        logging.error("Contour file not found: %s", filepath)
        sys.exit(1)
    gdf = gpd.read_file(filepath).to_crs(epsg=epsg_code)
    logging.info("Loaded contour: %s", filepath)
    return gdf

# -----------------------------------------------------------------------------
# Step 2: Compute cell size in decimal degrees
# -----------------------------------------------------------------------------
def get_extents(
    geo_df: gpd.GeoDataFrame
) -> tuple[float, float, float, float]:
    """
    Get bounding box coordinates (xmin, ymin, xmax, ymax).

    Args:
        geo_df (GeoDataFrame): Input GeoDataFrame.

    Returns:
        tuple: xmin, ymin, xmax, ymax.
    """
    xmin, ymin, xmax, ymax = geo_df.total_bounds
    return xmin, ymin, xmax, ymax


def calculate_cell_size(
    contour: gpd.GeoDataFrame,
    cell_km: float
) -> tuple[float, float]:
    """
    Calculate cell side lengths in decimal degrees for latitude and longitude.

    Args:
        contour (GeoDataFrame): Boundary GeoDataFrame to derive mid-latitude.
        cell_km (float): Desired side length in kilometers.

    Returns:
        tuple: lat_step, lon_step in degrees.
    """
    lat_step = cell_km / 111.32
    _, ymin, _, ymax = get_extents(contour)
    mid_lat = (ymin + ymax) / 2
    lon_step = lat_step / np.cos(np.deg2rad(mid_lat))
    return lat_step, lon_step

# -----------------------------------------------------------------------------
# Step 3: Generate grid origin points
# -----------------------------------------------------------------------------
def generate_grid(
    contour: gpd.GeoDataFrame,
    cell_km: float
) -> pd.DataFrame:
    """
    Create DataFrame of southwest corner coordinates for each cell.

    Args:
        contour (GeoDataFrame): Boundary GeoDataFrame.
        cell_km (float): Side length in kilometers.

    Returns:
        DataFrame: Columns [grid_id, lat, lon].
    """
    xmin, ymin, xmax, ymax = get_extents(contour)
    lat_step, lon_step = calculate_cell_size(contour, cell_km)
    rows = []
    grid_id = 0
    lat = ymin
    while lat <= ymax:
        lon = xmin
        while lon <= xmax:
            rows.append({
                'grid_id': grid_id,
                'lat': round(lat, 6),
                'lon': round(lon, 6)
            })
            grid_id += 1
            lon += lon_step
        lat += lat_step
    df = pd.DataFrame(rows, columns=['grid_id', 'lat', 'lon'])
    logging.info("Generated %d grid points", len(df))
    return df

# -----------------------------------------------------------------------------
# Step 4: Convert origins to square polygons
# -----------------------------------------------------------------------------
def df_to_geodf(
    df: pd.DataFrame,
    epsg_code: int,
    contour: gpd.GeoDataFrame,
    cell_km: float
) -> gpd.GeoDataFrame:
    """
    Convert DataFrame of origins to GeoDataFrame of square polygons.

    Args:
        df (DataFrame): Contains 'lat' and 'lon' for cell corners.
        epsg_code (int): Target CRS EPSG code.
        contour (GeoDataFrame): Boundary for cell size ref.
        cell_km (float): Side length in kilometers.

    Returns:
        GeoDataFrame: Polygons of grid cells.
    """
    lat_step, lon_step = calculate_cell_size(contour, cell_km)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=df.apply(
            lambda r: box(r.lon, r.lat, r.lon + lon_step, r.lat + lat_step),
            axis=1
        ),
        crs=f"EPSG:{epsg_code}"  # geographic
    )
    return gdf

# -----------------------------------------------------------------------------
# Step 5: Filter cells inside contour
# -----------------------------------------------------------------------------
def filter_inside_contour(
    gdf: gpd.GeoDataFrame,
    contour: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Keep only cells that intersect the boundary contour.

    Args:
        gdf (GeoDataFrame): All grid cell polygons.
        contour (GeoDataFrame): Boundary polygon.

    Returns:
        GeoDataFrame: Filtered cells.
    """
    unioned = contour.unary_union
    clipped = gdf[gdf.geometry.intersects(unioned)].copy()
    clipped.reset_index(drop=True, inplace=True)
    logging.info("Filtered to %d cells within contour", len(clipped))
    return clipped

# -----------------------------------------------------------------------------
# Step 6: Main - generate and export grid
# -----------------------------------------------------------------------------
def main(
    contour_path: str,
    epsg_code: int,
    cell_km: float,
    output_path: str = OUTPUT_PATH
) -> None:
    """
    Generate grid and save to GeoPackage.

    Args:
        contour_path (str): Path to boundary GeoPackage.
        epsg_code (int): EPSG code for output grid CRS.
        cell_km (float): Side length of grid cells in km.
        output_path (str): Destination GeoPackage path.
    """
    contour = load_geopackage(Path(contour_path), epsg_code)
    df_grid = generate_grid(contour, cell_km)
    gdf_grid = df_to_geodf(df_grid, epsg_code, contour, cell_km)
    filtered = filter_inside_contour(gdf_grid, contour)

    out_fp = Path(output_path)
    filtered.to_file(out_fp, driver='GPKG', layer=out_fp.stem)
    logging.info("Grid exported to %s", out_fp)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate spatial grid')
    parser.add_argument('contour_file', help='GeoPackage boundary file')
    parser.add_argument('epsg_code', type=int, help='EPSG CRS code')
    parser.add_argument('cell_km', type=float, help='Cell side in km')
    parser.add_argument(
        'output_path',
        nargs='?',
        default=OUTPUT_PATH,
        help='Output GeoPackage path'
    )
    args = parser.parse_args()
    main(args.contour_file, args.epsg_code, args.cell_km, args.output_path)
