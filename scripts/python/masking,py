import ee

masks = ['New_York_v1']

def generate_qa_mask_v1(year, geometry):
    qa_masks = ee.ImageCollection(f'projects/ee-cjc378/assets/qa_masks_New_York')
    year_masks = {2019:1056, 2020:2144, 2021:4320, 2022:8672, 2023:17376}
    mask_value = ee.Number(2).pow(15).add(ee.Number(year_masks[year])).toUint16()
    qa = qa_masks.filterBounds(geometry).mosaic()
    qa_mask = qa.bitwiseAnd(mask_value).eq(mask_value)
    return qa_mask