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
    main(input_grid, output_html)
"""
# %% Imports
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
    Create a Folium Map object, optionally save to HTML,
    and return the Map for display.

    Args:
        gdf (GeoDataFrame): Grid with 'GaussianMixture' and 'score_riqueza'.
        output_html (Path): Path to save the HTML map.
    """
    colors = {
        '0.0': '#49E973',
        '1.0': '#A8B47E',
        '2.0': '#51D3E1',
        'Sin datos': '#4D4D4D'
        }
    gdf_wgs = gdf.to_crs(epsg=4326)
    center = [gdf_wgs.geometry.centroid.y.mean(),
              gdf_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=7, tiles='cartodbpositron')
    Fullscreen().add_to(m)

    def style_func(feature):
        props = feature['properties']
        cluster = props.get('GaussianMixture', 'Sin datos')
        color = colors.get(cluster, '#f0f0f0')
        opacity = props.get('opacidad_categoria', 0.7)
        return {'fillColor': color, 'color': color, 'weight': 0.5,
                'fillOpacity': opacity}
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
    output_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_html)
    logging.info("Saved interactive map to %s", output_html)
    return m


# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------
def main() -> None:
    """
    Load fixed grid file and generate map.
    """
    input_grid = Path('../data/processed/grilla_riqueza.gpkg')
    output_html = Path('../reports/figures/mapa_interactivo.html')
    if not input_grid.exists():
        logging.error("Grid not found: %s", input_grid)
        sys.exit(1)
    gdf = gpd.read_file(input_grid)
    logging.info("Loaded enriched grid: %s", input_grid)
    m = make_folium_map(gdf, output_html)
    return m


if __name__ == '__main__':
    main()
