#!/usr/bin/env python3
"""
Script para descargar datos geoespaciales de la comuna seleccionada.
"""

import os
import sys
import click
import requests
import geopandas as gpd
import osmnx as ox
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataDownloader:
    """Clase para gestionar la descarga de datos geoespaciales."""

    def __init__(self, comuna_name: str, output_dir: Path):
        self.comuna = comuna_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Inicializando descarga para comuna: {comuna_name}")

    def download_osm_data(self):
        """Descarga datos de OpenStreetMap usando OSMnx."""
        try:
            logger.info("Descargando red vial desde OSM...")

            # Configurar OSMnx
            ox.config(use_cache=True, log_console=True)

            # Descargar red vial
            place_query = f"{self.comuna}, Chile"
            G = ox.graph_from_place(place_query, network_type='all')

            # Guardar grafo
            output_file = self.output_dir / 'osm_network.graphml'
            ox.save_graphml(G, output_file)
            logger.info(f"Red vial guardada en: {output_file}")

            # Descargar edificios
            logger.info("Descargando edificios...")
            buildings = ox.geometries_from_place(
                place_query,
                tags={'building': True}
            )

            # Guardar edificios
            buildings_file = self.output_dir / 'osm_buildings.geojson'
            buildings.to_file(buildings_file, driver='GeoJSON')
            logger.info(f"Edificios guardados en: {buildings_file}")

            # Descargar amenidades
            logger.info("Descargando amenidades...")
            amenities = ox.geometries_from_place(
                place_query,
                tags={'amenity': True}
            )

            amenities_file = self.output_dir / 'osm_amenities.geojson'
            amenities.to_file(amenities_file, driver='GeoJSON')
            logger.info(f"Amenidades guardadas en: {amenities_file}")

            return True

        except Exception as e:
            logger.error(f"Error descargando datos OSM: {e}")
            return False

    def download_boundaries(self):
        """Descarga límites administrativos de IDE Chile."""
        try:
            logger.info("Descargando límites administrativos...")

            # URL del servicio WFS de IDE Chile (ejemplo)
            wfs_url = "https://www.ide.cl/geoserver/wfs"

            # Parámetros para la petición
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typeName': 'division_comunal',
                'outputFormat': 'application/json',
                'CQL_FILTER': f"comuna='{self.comuna.upper()}'"
            }

            # Realizar petición
            response = requests.get(wfs_url, params=params)

            if response.status_code == 200:
                # Guardar respuesta
                boundaries_file = self.output_dir / 'comuna_boundaries.geojson'
                with open(boundaries_file, 'w') as f:
                    f.write(response.text)
                logger.info(f"Límites guardados en: {boundaries_file}")
                return True
            else:
                logger.warning("No se pudieron descargar límites de IDE Chile")
                return False

        except Exception as e:
            logger.error(f"Error descargando límites: {e}")
            return False

    def create_metadata(self):
        """Crea archivo de metadatos de la descarga."""
        metadata = {
            'comuna': self.comuna,
            'fecha_descarga': datetime.now().isoformat(),
            'fuentes': ['OpenStreetMap', 'IDE Chile'],
            'archivos_generados': list(self.output_dir.glob('*'))
        }

        metadata_file = self.output_dir / 'metadata.txt'
        with open(metadata_file, 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")

        logger.info(f"Metadatos guardados en: {metadata_file}")


@click.command()
@click.option('--comuna', required=True, help='Nombre de la comuna')
@click.option('--output', default='../data/raw', help='Directorio de salida')
@click.option('--sources', default='all', help='Fuentes a descargar (osm,ide,all)')
def main(comuna, output, sources):
    """Script principal para descarga de datos."""

    logger.info("=" * 50)
    logger.info("INICIANDO DESCARGA DE DATOS")
    logger.info("=" * 50)

    downloader = DataDownloader(comuna, Path(output))

    # Descargar según las fuentes especificadas
    if sources in ['osm', 'all']:
        downloader.download_osm_data()

    if sources in ['ide', 'all']:
        downloader.download_boundaries()

    # Crear metadatos
    downloader.create_metadata()

    logger.info("Descarga completada exitosamente!")


if __name__ == '__main__':
    main()
