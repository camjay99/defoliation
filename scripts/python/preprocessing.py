import ee

sources = ['Sentinel2', 'Landsat', 'MODIS', 'HLS']
resolutions = {'Sentinel2':10, 'Landsat':30, 'MODIS':250, 'HLS':30}    

def rescale_years(col, start_year, end_year):
    def rescale(year):
        year = ee.Number(year)
        start = ee.Date.fromYMD(year,1,1)
        end   = ee.Date.fromYMD(year.add(1),1,1)
        year_max = col.select('EVI').filterDate(start, end).max()
        return (col.filterDate(start, end)
                .map(lambda image: 
                        image.addBands(
                            image.select('EVI').divide(year_max).rename('EVI_scaled')).copyProperties(image, ['system:time_start'])))

    years = ee.List.sequence(start_year, end_year)
    col_scaled = ee.ImageCollection(ee.FeatureCollection(years.map(rescale)).flatten())
    return col_scaled.select(['doy', 'EVI_scaled'])

def preprocess_Landsat(start_date, end_date, geometry, phenology=None):
    def applyScaleFactors(image):
        # Bits 4 and 3 are cloud shadow and cloud, respectively.
        cloudShadowBitMask = 1 << 4
        cloudsBitMask = 1 << 3
        # Get the pixel QA band.
        qa = image.select('QA_PIXEL')
        # Both flags should be set to zero, indicating clear conditions.
        mask = (qa.bitwiseAnd(cloudShadowBitMask).eq(0)
                .And(qa.bitwiseAnd(cloudsBitMask).eq(0)))
            
        
        opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        return (image.addBands(opticalBands, None, True) 
                    .updateMask(mask).copyProperties(image, ['system:time_start']))

    l7 = (ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .map(applyScaleFactors))
    l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .map(applyScaleFactors))

    def harmonizeL7(image):
        return image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']).copyProperties(image, ['system:time_start'])

    def harmonizeL8(image):
        return image.select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2'])

    # Map harmonizations and create combined collection
    l7 = l7.map(harmonizeL7)
    l8 = l8.map(harmonizeL8)
    ls = l7.merge(l8)

    ## Calculate EVI and masks
    nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')

    def preprocess(image):
        # New bands
        EVI = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
            {
                'NIR': image.select('NIR'),
                'RED': image.select('RED'),
                'BLUE': image.select('BLUE')
            }).rename('EVI')
        
        doy = image.date().getRelative('day', 'year')
        doy_band = ee.Image.constant(doy).uint16().rename('doy')
        
        # Masks
        mask = EVI.lte(1).And(EVI.gte(0))
        if phenology == None:
            mask = mask.And(doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS'))))
        
        # Return the masked image with EVI bands.
        return (image.addBands(ee.Image([EVI, doy_band]))
                    #.updateMask(forest_mask)
                    .updateMask(mask)
                    .copyProperties(image, ['system:time_start']))

    ls = ls.map(preprocess)
    return ls.select(['doy', 'EVI'])

def preprocess_MODIS(start_date, end_date, geometry, phenology=None):
    # Load IGBP MODIS land cover classifications
    landcover = (ee.ImageCollection("MODIS/061/MCD12Q1")
                   .select('LC_Type1')
                   .filter(ee.Filter.eq('system:index', '2016_01_01'))
                   .first())

    def prepareTimeSeries(image):
        withObs = image.select('num_observations_1km').gt(0)
        QA = image.select('state_1km')
        snowMask = QA.bitwiseAnd(1 << 15).eq(0).rename('snowMask')
        shadowMask = QA.bitwiseAnd(1 << 2).eq(0)
        cloudMask = QA.bitwiseAnd(1 << 10).eq(0)
        cirrusMask1 = QA.bitwiseAnd(1 << 8).eq(0)
        cirrusMask2 = QA.bitwiseAnd(1 << 9).eq(0)
        mask = (cirrusMask1.And(cirrusMask2).And(cloudMask)
                .And(shadowMask).And(snowMask))

        EVI = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
            {
                'NIR': image.select('sur_refl_b02').divide(10000),
                'RED': image.select('sur_refl_b01').divide(10000),
                'BLUE': image.select('sur_refl_b03').divide(10000)
            }).rename('EVI');
        doy = image.date().getRelative('day', 'year')
        doy_band = ee.Image.constant(doy).uint16().rename('doy')
        
        mask = EVI.lte(1).And(EVI.gte(0))
        if phenology != None:
            mask = mask.And((doy_band.gte(phenology.select('SoS'))
                      .And(doy_band.lte(phenology.select('EoS')))))

        return (image.addBands(ee.Image([EVI, doy_band]))
                    .addBands(image.metadata('system:time_start','date1'))
                    .updateMask(withObs)
                    .updateMask(mask)
                    .copyProperties(image))

    col = (ee.ImageCollection('MODIS/061/MOD09GQ')
             .linkCollection(ee.ImageCollection("MODIS/061/MOD09GA"), 
                             ["num_observations_1km", "state_1km", "sur_refl_b03"])
             .filterDate(start_date, end_date)
             .filterBounds(geometry)
             .map(prepareTimeSeries))
    return col

def preprocess_Sentinel2(start_date, end_date, geometry, phenology=None):
    # Cloud Score+ image collection.
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
    QA_BAND = 'cs_cdf'
    CLEAR_THRESHOLD = 0.65

    # Load NLCD 2019 landcover map
    nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')

    def preprocess(image):
        # New Bands
        image_s = image.divide(10000)
        EVI = image_s.expression(
            '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
                'NIR': image_s.select('B8'),
                'RED': image_s.select('B4'),
                'BLUE': image_s.select('B2')
            }).rename('EVI')
        doy = image.date().getRelative('day', 'year').add(1)
        doy_band = ee.Image.constant(doy).uint16().rename('doy')

        # Masks
        mask = mask.And(EVI.lte(1).And(EVI.gte(0)))
        if phenology != None:
            mask = mask.And(doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS'))))
        mask = mask.And(image.select(QA_BAND).gte(CLEAR_THRESHOLD))


        return (image.addBands(ee.Image([EVI, doy_band]))
                     .updateMask(mask)
                     .copyProperties(image, ['system:time_start']))

    # Harmonized Sentinel-2 Level 2A collection.
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess))
    return s2

def preprocess_HLS(start_date, end_date, geometry, phenology=None):
    # Load HLS S30/L30
    collection_L30 = (ee.ImageCollection("NASA/HLS/HLSL30/v002")
                        .filterDate(start_date, end_date)
                        .filterBounds(geometry))
                    
    collection_S30 = (ee.ImageCollection("NASA/HLS/HLSS30/v002")
                        .filterDate(start_date, end_date)
                        .filterBounds(geometry))

    # Rename bands so collections can be used together.
    def rename_bands_L30(image):
        return image.select(['B2','B4','B5', 'Fmask'],['BLUE', 'RED', 'NIR', 'Fmask'])

    def rename_bands_S30(image):
        return image.select(['B2','B4','B8', 'Fmask'],['BLUE', 'RED', 'NIR', 'Fmask'])
        
    def preprocess(image):
        # New Bands
        EVI = image.expression(
            '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
                'NIR': image.select('NIR'),
                'RED': image.select('RED'),
                'BLUE': image.select('BLUE')
            }).rename('EVI')
        doy = image.date().getRelative('day', 'year')
        doy_band = ee.Image.constant(doy).uint16().rename('doy')
        
        # Masks
        cloud_mask_val = ee.Number.parse("00101110", 2)
        mask = image.select("Fmask").bitwiseAnd(cloud_mask_val).eq(0) # Cloud Mask
        mask = mask.And(EVI.lte(1).And(EVI.gte(0))) # EVI mask
        if phenology != None:
            mask = mask.And(doy_band.gte(phenology.select('SoS')) # Phenology Mask
                            .And(doy_band.lte(phenology.select('EoS'))))

        return (ee.Image([EVI, doy_band])
                     .updateMask(mask)
                     .copyProperties(image, ['system:time_start']))

    collection_L30 = collection_L30.map(lambda image: preprocess(rename_bands_L30(image)))
    collection_S30 = collection_S30.map(lambda image: preprocess(rename_bands_S30(image)))

    return collection_L30.merge(collection_S30)
    