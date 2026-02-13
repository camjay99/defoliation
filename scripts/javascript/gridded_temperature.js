var new_york = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM1_NAME', 'New York')).geometry();
var grid = new_york.coveringGrid('EPSG:5070', 10000);

var daymet = ee.ImageCollection("NASA/ORNL/DAYMET_V4");
daymet = daymet.filterDate('1980-01-01', '2024-01-01').filterBounds(new_york);

function get_temperature_month(target_year, month) {
  var start_of_defol = ee.Date.fromYMD(ee.Number(target_year), 6, 1);
  var start_of_obs = start_of_defol.advance(ee.Number(month).multiply(-1), 'month');
  var end_of_obs = start_of_defol.advance(ee.Number(month-1).multiply(-1), 'month');
  var start_doy = start_of_obs.getRelative('day', 'year').add(1);
  var end_doy = end_of_obs.getRelative('day', 'year');
  var days = end_doy.subtract(start_doy).add(2);
  
  var tmax_coll = daymet.select('tmax').filter(ee.Filter.dayOfYear(start_doy, end_doy));
  // Using 44 years of data, divide by 43 to get mean maximum temperature in this period
  var tmax_mean = tmax_coll.sum().divide(44).rename('tmax_mean_' + month);
  var tmax_recent = tmax_coll.filterDate(start_of_obs, end_of_obs).sum().rename('tmax_recent_' + month);
  var tmax_anom = tmax_recent.subtract(tmax_mean).rename('tmax_anom_' + month);
  
  var tmax_data = ee.Image([tmax_mean, tmax_recent, tmax_anom]);
  var grid_stats = tmax_data.reduceRegions({
    collection: grid,
    reducer: ee.Reducer.mean(),
    crs: 'EPSG:5070',
    scale: 1000
  });
  
  grid_stats = grid_stats.map(
    function (f) {return f.set('days', days);});

  Export.table.toDrive({
    collection: grid_stats,
    description: 'tmax_grid_' + target_year + '_month_' + month,
    folder: 'Defoliation',
    fileFormat: 'geojson',
    selectors: ['system:index', 'tmax_mean_' + month, 'tmax_recent_' + month, 'tmax_anom_' + month, 'days', '.geo']
  });
}

for (var i = 1; i <= 24; i++) {
  get_temperature_month(2023, i);
}