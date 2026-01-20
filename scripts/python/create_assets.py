##########################################################
# Registers COGs saved in Google Cloud Storage as assets
# in Google Earth Engine.
##########################################################

import argparse
import json
from pprint import pprint
import time

import ee
from google.auth.transport.requests import AuthorizedSession

import geometries
import preprocessing


##############################################################
# Parse arguments
##############################################################

parser = argparse.ArgumentParser(
    description='Options for calculating growing season')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The project COGs are located in. 
# You may be prompted to authenticate.
parser.add_argument('--project', '-p', action='store', 
                    default=None, required=True)

# Parse arguments provided to script
args = parser.parse_args()


##############################################################
# Initialize Google Earth Engine API
##############################################################

try:
    ee.Initialize(project=args.project)
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project=args.project)

session = AuthorizedSession(
    ee.data.get_persistent_credentials().with_quota_project(args.project)
)
url = f'https://earthengine.googleapis.com/v1alpha/projects/{args.project}/image:importExternal'

##############################################################
# Create Image Manifests
##############################################################

with open('image_manifests.json', 'r') as f:
    image_manifests = json.load(f)

    for i in image_manifests:
        request = {
            'imageManifest': image_manifests[i],
            "overwrite": True
        }

        if args.submit:
            response = session.post(
                url=url,
                data=json.dumps(request)
            )

            pprint(json.loads(response.content))

            if not response:
                break