// AOI: reemplaza con tu asset uploadado
var aoi = ee.FeatureCollection('users/isidorareveco/limite_gee');

// Parámetros
var start = '2022-01-01';
var end = '2022-12-31';
var scale = 10;
var crsOut = 'EPSG:3857';
var exportFolder = 'GEE_Exports';
var filePrefix = 'sanbernardo_indices_2022';

// Máscara usando SCL
function maskS2_scl(image) {
  var scl = image.select('SCL');
  var mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  // Mantener bandas reflectancia y máscaras; escalar reflectancias
  return image.updateMask(mask).divide(10000);
}

// Añadir índices y castear cada uno a Float32
function addIndices(img) {
  var nir = img.select('B8');
  var red = img.select('B4');
  var green = img.select('B3');
  var blue = img.select('B2');
  var swir1 = img.select('B11');

  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI').toFloat();
  var evi = nir.subtract(red).multiply(2.5)
            .divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1))
            .rename('EVI').toFloat();
  var L = 0.5;
  var savi = nir.subtract(red).multiply(1 + L)
             .divide(nir.add(red).add(L)).rename('SAVI').toFloat();
  var ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI').toFloat();
  var mndwi = green.subtract(swir1).divide(green.add(swir1)).rename('MNDWI').toFloat();

  return img.addBands([ndvi, evi, savi, ndwi, mndwi]);
}

// Cargar colección Sentinel-2 SR
var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterDate(start, end)
  .filterBounds(aoi)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
  .map(maskS2_scl)
  .map(addIndices);

// (Opcional) comprobar tipos de bandas de la primera imagen (debug)
print('First image band types:', s2.first().bandTypes());
// Crear composite: mediana de índices
var indices = s2.select(['NDVI', 'EVI', 'SAVI', 'NDWI', 'MNDWI']).median().clip(aoi);

// Comprobar tipos en el composite
print('Composite band types:', indices.bandTypes());

// Mostrar en mapa
Map.centerObject(aoi, 12);
Map.addLayer(indices.select('NDVI'), {min:0, max:1, palette:['white','yellow','green']}, 'NDVI median');

// Export multibanda: forzar Float32 por si acaso y usar bounds() para evitar tile errors
var exportRegion = aoi.geometry().bounds();
var combined = indices.select(['NDVI','EVI','SAVI','NDWI','MNDWI']).toFloat().clip(aoi);

Export.image.toDrive({
  image: combined,
  description: filePrefix + '_ALL_INDICES',
  folder: exportFolder,
  fileNamePrefix: filePrefix + '_ALL_INDICES',
  region: exportRegion,
  scale: scale,
  crs: crsOut,
  maxPixels: 1e13
});