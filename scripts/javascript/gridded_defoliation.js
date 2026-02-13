var project = '<insert project here>';

var landcover = ee.ImageCollection("USGS/NLCD_RELEASES/2019_REL/NLCD");
var defol_2020 = ee.Image("projects/"+project+"/assets/scores_mask_2020");
var defol_2021 = ee.Image("projects/"+project+"/assets/scores_mask_2021");
var defol_2022 = ee.Image("projects/"+project+"/assets/scores_mask_2022");
var defol_2023 = ee.Image("projects/"+project+"/assets/scores_mask_2023");

// Create a common grid for extracting summary statistics.
var new_york = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM1_NAME', 'New York')).geometry();
var grid = new_york.coveringGrid('EPSG:5070', 10000);

// Specify the year and data layer to use.
var year = 2020
var defol = defol_2020

// Save system:index as a separate property so it can be retrieved after the join.
grid = grid.map(
  function (feature) {
    return feature.set('id', feature.get('system:index'));
  });

// Prepare relevant forest characteristics.
var landcover_2019 = landcover.filter(ee.Filter.eq('system:index', '2019')).first().select('landcover').clip(new_york);
var forest_2019 = landcover_2019.gte(41).and(landcover_2019.lte(43)).multiply(ee.Image.pixelArea()).rename('forest');
var deciduous_2019 = landcover_2019.eq(41).multiply(ee.Image.pixelArea()).rename('deciduous');
forest_2019 = ee.Image([forest_2019, deciduous_2019]);

// Get grid level forest characteristics.
var grid_forest = forest_2019.reduceRegions({
  collection: grid,
  reducer: ee.Reducer.sum(),
  crs: 'EPSG:5070',
  scale: 30
});

// Get grid level defoliation characteristics.
var grid_defol = defol.multiply(ee.Image.pixelArea()).reduceRegions({
  collection: grid,
  reducer: ee.Reducer.sum(),
  crs: 'EPSG:5070',
  scale: 10
});

// Join forest and defoliation information together.
var joinFilter = ee.Filter.equals({
  leftField: 'system:index',
  rightField: 'system:index'
});
var innerJoin = ee.Join.inner();
var grid_stats = innerJoin.apply(grid_forest, grid_defol, joinFilter);


// Prepare feature collection for export.
grid_stats = grid_stats.map(
  function (feature) {
    var primary = ee.Feature(feature.get('primary'));
    var secondary = ee.Feature(feature.get('secondary'));
    return ee.Feature(primary.geometry(), {'id':primary.get('id'), 
                             'forest':primary.get('forest'),
                             'deciduous':primary.get('deciduous'),
                             'defoliation_2':secondary.get('score_2'),
                             'qa_mask_2':secondary.get('qa_mask_2'),
                             'defoliation_3':secondary.get('score_3'),
                             'qa_mask_3':secondary.get('qa_mask_3')
    });
  });
  
Export.table.toDrive({
  collection: grid_stats,
  description: 'forest_grid_' + year,
  folder: 'Defoliation',
  fileFormat: 'GeoJSON',
  selectors: ['id', 'forest', 'deciduous', 'defoliation_2', 'qa_mask_2', 'defoliation_3', 'qa_mask_3', '.geo']
});