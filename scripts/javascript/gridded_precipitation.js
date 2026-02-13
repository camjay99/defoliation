var new_york = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM1_NAME', 'New York')).geometry();
var grid = new_york.coveringGrid('EPSG:5070', 10000);

var daymet = ee.ImageCollection("NASA/ORNL/DAYMET_V4");
daymet = daymet.filterDate('1980-01-01', '2024-01-01').filterBounds(new_york);

function get_precipitation_month(target_year, month) {
  var start_of_defol = ee.Date.fromYMD(ee.Number(target_year), 6, 1);
  var start_of_obs = start_of_defol.advance(ee.Number(month).multiply(-1), 'months');
  var end_of_obs = start_of_defol.advance(ee.Number(month-1).multiply(-1), 'months');
  var start_doy = start_of_obs.getRelative('day', 'year').add(1);
  var end_doy = end_of_obs.getRelative('day', 'year');
  var days = end_doy.subtract(start_doy).add(2);
  
  var prcp_coll = daymet.select('prcp').filter(ee.Filter.dayOfYear(start_doy, end_doy));
  // Using 44 years of data, divide by 43 to get mean total precipitation in this period
  var prcp_mean = prcp_coll.sum().divide(44).rename('prcp_mean_' + month);
  var prcp_recent = prcp_coll.filterDate(start_of_obs, end_of_obs).sum().rename('prcp_recent_' + month);
  var prcp_anom = prcp_recent.subtract(prcp_mean).rename('prcp_anom_' + month);
  
  var prcp_data = ee.Image([prcp_mean, prcp_recent, prcp_anom]);
  var grid_stats = prcp_data.reduceRegions({
    collection: grid,
    reducer: ee.Reducer.mean(),
    crs: 'EPSG:5070',
    scale: 1000
  });
  
  grid_stats = grid_stats.map(
    function (f) {return f.set('days', days);});

  Export.table.toDrive({
    collection: grid_stats,
    description: 'prcp_grid_' + target_year + '_month_' + month,
    folder: 'Defoliation',
    fileFormat: 'geojson',
    selectors: ['system:index', 'prcp_mean_' + month, 'prcp_recent_' + month, 'prcp_anom_' + month, 'days', '.geo']
  });
}

for (var i = 1; i <= 24; i++) {
  get_precipitation_month(2021, i);
}