Lagged climatic drivers of spongy moth (Lymantria dispar dispar) outbreaks revealed by satellite-based defoliation mapping.
===========================================================================================================================

These codes are used to generate datasets and figures for our in preparation paper. Below to a complete guide on how to run the code and which scripts need to be run to generate each figure.

Required packages
-----------------

* [earthengine-api](https://developers.google.com/earth-engine/guides/python_install)
* [Ultraplot](https://ultraplot.readthedocs.io/en/latest/install.html)
* [Pandas](https://pandas.pydata.org/getting_started.html)
* [GeoPandas](https://geopandas.org/en/stable/getting_started.html)
* [Rasterio](https://rasterio.readthedocs.io/en/stable/installation.html)

Running the code
----------------

All python files are designed to be run from the command line. For javascript files, copy the code into the GEE code editor to run it. Figures are made in jupyter notebooks.

Most figures depend on the outputs from the basic pipeline. This can be run using the following sample commands:
1. `python 0_maximum_separation.py --project=<project name> --state="New York" --submit`
2. `python 1_1_trends_theilsen.py --project=<project name> --state="New York" --submit`
3. `python 2_1_defoliation_theilsen.py --project=<project name> --state="New York" --submit`
4. `python 3_classify_denoise.py --project=<project name> --state="New York" --submit`

This will generate defoliation maps for all of New York. In addition, for specific site (Mt. Pleasant, Arnot Forest, Allegheny Reservoir, and Turkey Hill), a few other pipelines need to be run for the method comparison.

1. `python 1_2_trends_harmonic.py --project=<project name> --state="New York" --submit`
2. `python 2_2_defoliation_harmonic.py --project=<project name> --state="New York" --submit`
3. `python 2_3_defoliation_means.py --project=<project name> --state="New York" --submit`

### Main Figures
#### Figure 1
1. study_site_images.js
2. F1_SampleSiteShowcase.ipynb

#### Figure 2
1. F2_FullMethodsGraphs.ipynb

#### Figure 3
1. study_site_images.js
2. F3_SampleSiteDefol.ipynb

#### Figure 4
1. gridded_defoliation.js
2. F4_YearlyExtent.ipynb

#### Figure 5
1. gridded_defoliation.js
2. gridded_precipitation.js
3. gridded_temperature.js
4. F5_LagCorrelations.ipynb

### Main Tables
#### Table 3
1. calculate_ROC.js

#### Table 4
1. defoliated_area.js

#### Table 5
1. gridded_defoliation.js
2. gridded_precipitation.js
3. gridded_temperature.js
4. T5_LagRegression.ipynb

### Supplementary Figures
#### Figure S1
1. study_site_images.js
2. FS1_LoggingShowcase.ipynb

#### Figure S2
1. evaluate_defoliaiton.js
2. FS2_ExampleClassification.ipynb

#### Figure S3
1. aerial_survey_comp_maps.js
2. FS3_2019Map.ipynb

#### Figure S4
1. aerial_survey_comp_maps.js
2. FS4_AerialSurveyStatewide.ipynb

#### Figure S5
1. aerial_survey_comp_maps.js
2. FS5_AerialSurveyStudySites.ipynb

#### Figure S6
1. gridded_defoliation.py
2. gridded_precipitation.py
3. gridded_temperature.py
4. T5_LagRegression.ipynb (to create predictions)
5. FS6_LagMaps.ipynb

### Supplementary Tables
#### Table S1-S4
1. calculate_ROC.js

#### Table S5
1. transition_matrix.py

#### Table S6/S7
1. T5_LagRegression.py 