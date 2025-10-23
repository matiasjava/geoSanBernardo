# crear y activar virtualenv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar streamlit y dependencias geoespaciales
pip install streamlit geopandas psycopg2-binary sqlalchemy geoalchemy2 folium streamlit-folium rasterio rasterstats

# congelar dependencias
pip freeze > requirements.txt