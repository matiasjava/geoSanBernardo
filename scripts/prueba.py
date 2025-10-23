from pathlib import Path
import osmnx as ox

# siempre base en el directorio del script, no en donde está el terminal
BASE = Path(__file__).resolve().parent
OUTDIR = BASE / "data" / "processed"
OUTDIR.mkdir(parents=True, exist_ok=True)  # crea data/processed si no existe

out_path = OUTDIR / "limite_san_bernardo.gpkg"

gdf_lim = ox.geocode_to_gdf("San Bernardo, Chile")
gdf_lim.to_file(out_path, layer="limite", driver="GPKG")

print(f"Guardado OK en: {out_path}")
