// This still refers to authors GEE copy, as it is someone else's dataset and cannot be republished.
var as = ee.FeatureCollection("projects/ee-cjc378/assets/aerial_survey");

for (var year = 2019; year <= 2023; year++) {
  var data = ee.Image('projects/ee-cjc378/assets/scores_mask_' + year);
  var new_york = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM1_NAME', 'New York'));
  var resolution = 10;
  var scale = 1000;
  
  var as_raster = as
    .filter(ee.Filter.eq('year', year))
    .reduceToImage({
      properties: ['year'],
      reducer: ee.Reducer.first()
    })
    .setDefaultProjection("EPSG:5070", null, resolution)
    .unmask().clip(new_york);
  
  var image = ee.Image([data, as_raster]).toFloat();
  
  Map.addLayer(as);
  Map.addLayer(image);
  
  Export.image.toDrive({
    image: image,
    description: 'as_satellite_comp_' + scale + '_' + year,
    folder: 'Defoliation',
    region: new_york.geometry(),
    scale: scale,
    crs: 'EPSG:5070',
    maxPixels: 1e13,
  });
}