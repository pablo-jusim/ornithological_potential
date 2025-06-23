# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

"""
Generate interactive Folium map(s) from enriched grid GeoPackage.

Steps:
1. Load enriched grid with richness scores
2. Create Folium map colored by cluster and richness score
3. Save HTML output

Usage:
    python postprocess_map.py \
        --input-grid data/processed/grilla_riqueza.gpkg \
        --output-html reports/figures/mapa_interactivo.html
"""
# %% Imports
import argparse
import sys
import logging
from pathlib import Path
import geopandas as gpd
import folium
from folium.plugins import Fullscreen


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
    gdf: gpd.GeoDataFrame,
    output_html: Path
) -> None:
    """
    Create and save an interactive Folium map.

    Args:
        gdf (GeoDataFrame): Grid with 'GaussianMixture' and 'score_riqueza'.
        output_html (Path): Path to save the HTML map.
    """
    # Define color palette
    colors = {
        '0.0': '#49E973',
        '1.0': '#A8B47E',
        '2.0': '#51D3E1',
        'Sin datos': '#4D4D4D'
    }
    # Convert to WGS84
    gdf_wgs = gdf.to_crs(epsg=4326)

    # Compute center
    center = [
        gdf_wgs.geometry.centroid.y.mean(),
        gdf_wgs.geometry.centroid.x.mean()
    ]

    m = folium.Map(
        location=center,
        zoom_start=7,
        tiles='cartodbpositron'
    )
    Fullscreen().add_to(m)

    def style_func(feature):
        props = feature['properties']
        cluster = props.get('GaussianMixture', 'Sin datos')
        color = colors.get(cluster, '#f0f0f0')
        opacity = props.get('opacidad_categoria', 0.7)
        return {
            'fillColor': color,
            'color': color,
            'weight': 0.5,
            'fillOpacity': opacity
        }

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

    folium.TileLayer(
        tiles='http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Ensure output directory exists
    output_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_html)
    logging.info("Saved interactive map to %s", output_html)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------
def main():
    """
    Main function to execute this script
    """
    parser = argparse.ArgumentParser(
        description="Generate interactive richness map from grid data"
    )
    parser.add_argument(
        '--input-grid',
        type=Path,
        default=Path('data/processed/grilla_riqueza.gpkg'),
        help='Path to enriched grid GeoPackage'
    )
    parser.add_argument(
        '--output-html',
        type=Path,
        default=Path('reports/figures/mapa_interactivo.html'),
        help='Path to save the HTML map'
    )
    args = parser.parse_args()

    # Load grid
    if not args.input_grid.exists():
        logging.error("Grid not found: %s", args.input_grid)
        sys.exit(1)
    gdf = gpd.read_file(args.input_grid)
    logging.info("Loaded enriched grid: %s", args.input_grid)

    # Create and save map
    make_folium_map(gdf, args.output_html)


if __name__ == '__main__':
    main()
