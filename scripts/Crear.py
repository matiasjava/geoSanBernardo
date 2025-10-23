from pathlib import Path
from sqlalchemy import create_engine
import geopandas as gpd
import osmnx as ox

# 1) Rutas ancladas al script
BASE = Path(__file__).resolve().parent
DATADIR = BASE / "data"
PROCESSED = DATADIR / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

GPKG = PROCESSED / "limite_san_bernardo.gpkg"
LAYER = "limite"

print(f"BASE: {BASE}")
print(f"Buscando GPKG en: {GPKG}")

# 2) Si no existe el GPKG, lo creo desde OSMnx
if not GPKG.exists():
    print("No existe el GPKG. Creándolo con OSMnx…")
    gdf_lim = ox.geocode_to_gdf("San Bernardo, Chile")
    # opcional: asegura CRS proyectado si quieres (ej: EPSG:32719). Aquí lo dejamos como viene (WGS84)
    gdf_lim.to_file(GPKG, layer=LAYER, driver="GPKG")
    print(f"Creado: {GPKG}")

# 3) Leo la capa desde el GPKG
gdf = gpd.read_file(GPKG, layer=LAYER)
print(f"Leídas {len(gdf)} geometrías. CRS: {gdf.crs}")

# 4) Conexión a PostGIS
engine = create_engine("postgresql://geouser:geopass@localhost:5432/geodatabase")

# 5) Subo a PostGIS (reemplaza si ya existía)
TABLE = "limite_san_bernardo"
gdf.to_postgis(TABLE, engine, if_exists="replace", index=False)
print(f"Tabla creada en PostGIS: {TABLE}")
