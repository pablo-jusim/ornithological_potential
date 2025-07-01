# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

"""
Generate interactive Folium map(s) from enriched grid GeoPackage.

Steps:
1. Load enriched grid with richness scores
2. Create Folium map colored by cluster and richness score
3. Save HTML output

Usage as script:
    python postprocess_map.py \
        --input-grid data/processed/grilla_riqueza.gpkg \
        --output-html reports/figures/mapa_interactivo.html

Importable API:
    from postprocess_map import main
    m = main()
    m  # returns folium.Map for notebook display
"""
# %% Imports
import sys
import logging
from pathlib import Path
import geopandas as gpd
import folium
from folium.plugins import Fullscreen
from utils import categorise_opacity, generate_cluster_colors

# %% Paths
BASE_DIR = Path(__file__).resolve().parent.parent
# Define input data path
INPUT_GRID = BASE_DIR / 'data' / 'processed' / 'grilla_riqueza.gpkg'
# Define output path for interactive map
OUTPUT_HTML = BASE_DIR / 'reports' / 'figures' / 'interactive_map.html'

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)


# -----------------------------------------------------------------------------
# Function to create Folium map
# -----------------------------------------------------------------------------
def make_folium_map(
    colors: dict,
    gdf: gpd.GeoDataFrame,
    output_html: Path
) -> folium.Map:
    """
    Create a Folium Map object, save to HTML, and return the Map for display.

    Args:
        colors (dict): Dictionary mapping cluster IDs to hex colors.
        gdf (GeoDataFrame): Grid with 'GaussianMixture' and 'score_riqueza'.
        output_html (Path): Path to save the HTML map.

    Returns:
        folium.Map: Interactive map object.
    """

    # Ensure cluster field is string
    gdf['GaussianMixture'] = (gdf['GaussianMixture']
                              .fillna('Without_data').astype(str))
    # Convert to WGS84
    gdf_wgs = gdf.to_crs(epsg=4326)
    # Compute center of map
    center = [
        gdf_wgs.geometry.centroid.y.mean(),
        gdf_wgs.geometry.centroid.x.mean()
    ]
    # Create Folium map
    m = folium.Map(location=center, zoom_start=7, tiles='cartodbpositron')
    Fullscreen().add_to(m)

    # Style function for GeoJson
    def style_func(feature):
        props = feature['properties']
        cluster = str(props.get('GaussianMixture', 'Without_data'))
        color = colors.get(cluster, '#f0f0f0')
        opacity = float(props.get('OpacityCategory', 0.7))
        return {
            'fillColor': color,
            'color': color,
            'weight': 0.5,
            'fillOpacity': opacity
        }

    # Add grid layer
    folium.GeoJson(
        gdf_wgs,
        name='Grid',
        style_function=style_func,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['GaussianMixture', 'score_riqueza'],
            aliases=['Cluster:', 'Score:'],
            localize=True
        )
    ).add_to(m)

    # Add satellite basemap
    folium.TileLayer(
        tiles='http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Save HTML file
    output_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_html)
    logging.info("Saved interactive map to %s", output_html)
    return m


# -----------------------------------------------------------------------------
# Main function with fixed paths
# -----------------------------------------------------------------------------
def main(cluster_count: int) -> folium.Map:
    """
    Load fixed grid file, generate and save map, and return Map object.

    Returns:
        folium.Map: Interactive map for display in notebooks.
    """

    if not INPUT_GRID.exists():
        logging.error("Grid not found: %s", INPUT_GRID)
        sys.exit(1)
    colors = generate_cluster_colors(cluster_count)
    # Read enriched grid
    gdf = gpd.read_file(INPUT_GRID)
    logging.info("Loaded enriched grid: %s", INPUT_GRID)
    gdf['OpacityCategory'] = gdf['score_riqueza'].apply(categorise_opacity)
    # Generate and save map, return object
    return make_folium_map(colors, gdf, OUTPUT_HTML)


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main(3)  # Example cluster count, can be adjusted
