import ee

site_names = ['Quabbin', 'Mt_Pleasant', 'Allegheny', 'Turkey_Point', 'Arnot_Forest']    

def get_geometry(site_name):
    match site_name:
        case 'Quabbin':
            # Quabbin Watershed, which experienced extensive defoliation in 2017
            return ee.Geometry.Polygon(
                [[[-72.46672740331262,42.27084785748798],
                  [-72.16254344335168,42.27084785748798],
                  [-72.16254344335168,42.47224049291286],
                  [-72.46672740331262,42.47224049291286]]], None, False)
        case 'Mt_Pleasant':
            # Mt Pleasant
            return ee.Geometry.Polygon(
                [[[-76.40472618414064, 42.48029198346047],
                  [-76.40472618414064, 42.3696708995445],
                  [-76.16963592840334, 42.3696708995445],
                  [-76.16963592840334, 42.48029198346047]]], None, False)
        case 'Allegheny':
            # Allegheny
            return ee.Geometry.Polygon(
                [[[-79.1986092128225, 42.249085326281715],
                  [-79.1986092128225, 41.72954071466429],
                  [-78.33343587297875, 41.72954071466429],
                  [-78.33343587297875, 42.249085326281715]]], None, False)
        case 'Turkey_point':
            # Turkey Point
            return ee.Geometry.Polygon(
                [[[-80.57997293051788, 42.649124560997215],
                  [-80.57997293051788, 42.61988855677763],
                  [-80.5315644222171, 42.61988855677763],
                  [-80.5315644222171, 42.649124560997215]]], None, False)
        case 'Arnot_Forest':
            # Arnot Forest
            return ee.Geometry.Polygon(
                [[[-76.68476578221755, 42.29975344583736],
                  [-76.68476578221755, 42.25466417545956],
                  [-76.60614487157302, 42.25466417545956],
                  [-76.60614487157302, 42.29975344583736]]], None, False)

def get_state(state):
    return ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level1").filter(ee.Filter.eq('ADM1_NAME', state)).geometry()