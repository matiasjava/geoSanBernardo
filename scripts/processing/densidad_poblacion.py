import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from sqlalchemy import create_engine
import folium
import branca.colormap as cm


def get_engine(db_url):
    return create_engine(db_url)


def load_manzanas(engine, table='public.manzanas_san_bernardo', geom_col='geom'):
    # Avoid selecting the geometry twice: SELECT * already includes the geom column
    sql = f"SELECT * FROM {table}"
    gdf = gpd.read_postgis(sql, con=engine, geom_col=geom_col)
    # Ensure the GeoDataFrame has a GeoSeries named 'geometry'
    try:
        gdf = gdf.set_geometry(geom_col)
    except Exception:
        # fallback: if geom_col already used as geometry, ignore
        pass
    # rename geometry column to the canonical name 'geometry' if needed
    if gdf.geometry.name != 'geometry':
        gdf = gdf.rename_geometry('geometry')
    return gdf


def ensure_crs_meters(gdf):
    # prefer EPSG:3857 for metric grid operations
    if gdf.crs is None:
        raise ValueError('GeoDataFrame sin CRS. Asigna CRS en la BD o en el script.')
    if gdf.crs.to_epsg() != 3857:
        return gdf.to_crs(epsg=3857)
    return gdf


def make_grid(gdf, cell_size=250):
    minx, miny, maxx, maxy = gdf.total_bounds
    xs = np.arange(minx, maxx + cell_size, cell_size)
    ys = np.arange(miny, maxy + cell_size, cell_size)
    polys = []
    ids = []
    idx = 0
    for x in xs[:-1]:
        for y in ys[:-1]:
            polys.append(box(x, y, x + cell_size, y + cell_size))
            ids.append(idx)
            idx += 1
    grid = gpd.GeoDataFrame({'gid': ids, 'geometry': polys}, crs=gdf.crs)
    return grid


def aggregate_grid(grid, manzanas, pop_col='total_pers'):
    # ensure population column numeric
    if pop_col not in manzanas.columns:
        raise ValueError(f'No existe columna {pop_col} en manzanas')
    # convert to numeric using pandas
    manzanas[pop_col] = pd.to_numeric(manzanas[pop_col], errors='coerce').fillna(0)
    # ensure geometry column is set
    manzanas = manzanas.set_geometry('geometry')
    # prepare left GeoDataFrame for spatial join (must include geometry)
    left = manzanas[[pop_col, 'geometry']].copy()
    left = gpd.GeoDataFrame(left, geometry='geometry', crs=manzanas.crs)
    sjoin = gpd.sjoin(left, grid, how='inner', predicate='intersects')
    agg = sjoin.groupby('gid')[pop_col].sum().reset_index().rename(columns={pop_col: 'pop'})
    grid = grid.merge(agg, on='gid', how='left')
    grid['pop'] = grid['pop'].fillna(0)
    return grid


def make_density_map(db_url, table='public.manzanas_san_bernardo', cell_size=250, show_limite=False, limite_table=None):
    """Connects to PostGIS, computes a grid aggregated population and returns a folium.Map
    If show_limite=True, attempts to read `limite_table` from the DB and overlay it in green.
    """
    engine = get_engine(db_url)
    manz = load_manzanas(engine, table=table)
    # ensure in meters
    manz = ensure_crs_meters(manz)

    # Try to read the administrative limit (used to define the grid extent)
    lim = None
    lt = limite_table or 'public.limite_3857'
    try:
        lim = gpd.read_postgis(f"SELECT * FROM {lt}", con=engine, geom_col='geom')
    except Exception:
        try:
            lim = gpd.read_postgis(f"SELECT * FROM {lt}", con=engine)
        except Exception:
            lim = None

    if lim is not None and not lim.empty:
        # ensure limite is in meters CRS for grid calculation
        try:
            lim = ensure_crs_meters(lim)
        except Exception:
            # if limite has no CRS, assume it's same as manz (already in 3857)
            lim = lim.set_crs(manz.crs, allow_override=True)
        # compute grid using limite bounds and clip to limite polygon
        grid = make_grid(lim, cell_size=cell_size)
        # clip to limite area (keep cells that intersect the limite)
        limite_union = lim.unary_union
        grid = grid[grid.intersects(limite_union)].copy()
    else:
        # fallback: use manz bounds for grid
        grid = make_grid(manz, cell_size=cell_size)

    # aggregate population into grid; cells without manzanas will become pop=0
    grid = aggregate_grid(grid, manz, pop_col='total_pers')

    # convert to EPSG:4326 for display
    grid_4326 = grid.to_crs(epsg=4326)
    manz_4326 = manz.to_crs(epsg=4326)

    # map center
    centroid = manz_4326.unary_union.centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=12, tiles='CartoDB positron')

    # color scale
    vmax = max(1, grid_4326['pop'].max())
    cmap = cm.LinearColormap(['yellow', 'orange', 'red'], vmin=1, vmax=vmax)
    cmap.caption = 'Población por celda'
    cmap.add_to(m)

    # add grid as geojson with style based on 'pop'
    def style_function(feature):
        pop = feature['properties'].get('pop', 0)
        if pop == 0 or pop is None:
            fillColor = '#2ca25f'  # green for empty cells
            fillOpacity = 0.6
        else:
            # use cmap for positive values
            try:
                fillColor = cmap(pop)
            except Exception:
                fillColor = '#ffffb2'
            fillOpacity = 0.8
        return {
            'fillColor': fillColor,
            'color': '#bbbbbb',
            'weight': 0.1,
            'fillOpacity': fillOpacity
        }

    folium.GeoJson(grid_4326.__geo_interface__, name='grid', style_function=style_function, tooltip=folium.GeoJsonTooltip(fields=['gid','pop'])).add_to(m)

    # optional: overlay manzanas boundaries semi-transparent
    folium.GeoJson(manz_4326.__geo_interface__, name='manzanas', style_function=lambda f: {'color':'#000000','weight':0.2,'fillOpacity':0}).add_to(m)
    # optional: overlay limite if requested
    if show_limite:
        lt = limite_table or 'public.limite_3857'
        try:
            # try common geometry column name 'geom'
            lim = gpd.read_postgis(f"SELECT * FROM {lt}", con=engine, geom_col='geom')
        except Exception:
            try:
                lim = gpd.read_postgis(f"SELECT * FROM {lt}", con=engine)
            except Exception:
                lim = None
        if lim is not None and not lim.empty:
            # ensure geometry column canonical
            try:
                if lim.geometry.name != 'geometry':
                    lim = lim.set_geometry(lim.geometry.name)
            except Exception:
                pass
            # transform to 4326 for display
            try:
                lim_4326 = lim.to_crs(epsg=4326)
            except Exception:
                lim_4326 = lim
            folium.GeoJson(lim_4326.__geo_interface__, name='limite', style_function=lambda f: {'color':'green','weight':2,'fillOpacity':0}).add_to(m)

    folium.LayerControl().add_to(m)

    # If limite was read, set map bounds to the limite (so map only shows San Bernardo)
    try:
        if 'lim' in locals() and lim is not None and not lim.empty:
            try:
                lim_4326 = lim.to_crs(epsg=4326)
            except Exception:
                lim_4326 = lim
            minx, miny, maxx, maxy = lim_4326.total_bounds
            # fit map to limite bounds (southWest, northEast)
            m.fit_bounds([[miny, minx], [maxy, maxx]])
            # also set maxBounds so user can't pan outside San Bernardo
            map_name = m.get_name()
            script = f"<script>{map_name}.setMaxBounds([[{miny}, {minx}], [{maxy}, {maxx}]]);</script>"
            m.get_root().html.add_child(folium.Element(script))
    except Exception:
        # if anything fails, ignore and return the map as-is
        pass
    return m
