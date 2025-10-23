import streamlit as st
import geopandas as gpd
import os
import sys
# ensure project root is on sys.path so 'scripts' can be imported from app/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from sqlalchemy import create_engine
from streamlit_folium import st_folium
import folium
from scripts.processing.densidad_poblacion import make_density_map

st.set_page_config(layout="wide", page_title="Análisis San Bernardo")

st.title("Dashboard San Bernardo - Demo")

# Ejemplo simple: leer GeoPackage local
st.sidebar.header("Controles")
db_url = st.sidebar.text_input("Postgres URL", value="postgresql://postgres:123456@localhost:5432/snbk")
show_limite = st.sidebar.checkbox("Mostrar límite de San Bernardo", value=False)


@st.cache_data(show_spinner=False)
def cached_make_map_html(db_url, table, cell_size, show_limite=False):
    # Generate folium map and return rendered HTML (safe to cache)
    m = make_density_map(db_url, table=table, cell_size=cell_size, show_limite=show_limite)
    # render to HTML string
    html = m.get_root().render()
    return html


if st.sidebar.button("Mostrar mapa densidad (generar)"):
    try:
        with st.spinner("Generando mapa de densidad desde la BD (cacheado)..."):
            m_html = cached_make_map_html(db_url, 'public.manzanas_san_bernardo', 250, show_limite=show_limite)
        st.success("Mapa generado")
        import streamlit.components.v1 as components
        components.html(m_html, height=800)
    except Exception as e:
        st.error(f"Error generando mapa de densidad: {e}")