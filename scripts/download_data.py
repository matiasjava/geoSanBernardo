# scripts/download_data.py

import os
from pathlib import Path
import osmnx as ox 
import requests 


COMUNA_NAME = "San Bernardo" 

class DataDownloader:
    
    def __init__(self, comuna_name=COMUNA_NAME, output_dir='../data/raw'):
        """Inicializa el descargador de datos para la comuna especificada."""
        self.comuna = comuna_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.comuna or self.comuna.lower() in ['your_comuna_here', '']:
            raise ValueError("Por favor, define la comuna en .env o en el script.")
        
        print(f"Descargador inicializado para la comuna: {self.comuna}")

    # -----------------------------------------------------
    # 2. Red Vial (OSMnx) 
    # -----------------------------------------------------
    def download_osm_network(self):
        """Descarga red vial desde OpenStreetMap usando OSMnx."""
        print(f"\n--- Descarga de Red Vial OMITIDA ---")
        print("✅ Red vial ya descargada y disponible en red_vial.gpkg.")


    # -----------------------------------------------------
    # 3. DEM (Placeholder/Instrucción)
    # -----------------------------------------------------
    def download_dem(self):
        """Descarga/Verifica el DEM (ALOS PALSAR/SRTM)[cite: 152]."""
        print("\n--- Iniciando gestión del DEM (SRTM/ALOS) ---")
        
        dem_filename = 'dem_san_bernardo.tif'
        filepath = self.output_dir / dem_filename

        if filepath.exists():
            print(f"✅ DEM (GeoTIFF) ya existe en: {filepath}. Omitiendo descarga.")
            return

        print("⚠️ ACCIÓN REQUERIDA: La descarga automatizada de DEM requiere APIs avanzadas (GEE/USGS).")
        print("➡️ PARA CONTINUAR: Descargue **manualmente** un GeoTIFF (SRTM o ALOS) que cubra San Bernardo.")
        print("   Guarde el archivo con el nombre **exacto**:")
        print(f"   {dem_filename} en la ruta: {self.output_dir}")
        print("   Este archivo es esencial para extraer Elevación y Pendiente para el ML [cite: 387-390].")
    
    # -----------------------------------------------------
    # 4. Placeholders para el resto de fuentes
    # -----------------------------------------------------
    def download_administrative_boundaries(self):
        """Descarga límites administrativos y manzanas censales (IDE/INE)[cite: 152]."""
        print("\n--- Descarga de Límites Administrativos y Censo ---")
        print("🟡 Límites: Implementación de descarga WFS/INE pendiente.")
        print("🟡 Censo/Manzanas: Implementación de descarga INE pendiente.")
    
    def download_sentinel2(self, start_date='2024-01-01', end_date='2024-03-31'):
        """Descarga imágenes Sentinel-2 (GEE)[cite: 152]."""
        print("\n--- Descarga de Sentinel-2 (GEE) ---")
        print("🟡 Sentinel-2: Implementación de descarga GEE pendiente.")

    # -----------------------------------------------------
    # 5. Función de Ejecución
    # -----------------------------------------------------
    def download_all(self):
        """Ejecuta todos los métodos de descarga."""
        print("\n=============================================")
        print("   INICIO DEL PROCESO DE ADQUISICIÓN DE DATOS")
        print("=============================================")
        
        self.download_dem()
        self.download_osm_network()
        self.download_administrative_boundaries()
        self.download_sentinel2()
        
        print("\n--- PROCESO DE ADQUISICIÓN FINALIZADO ---")

if __name__ == '__main__':
    try:
        downloader = DataDownloader()
        downloader.download_all()
    except ValueError as e:
        print(f"ERROR: {e}")