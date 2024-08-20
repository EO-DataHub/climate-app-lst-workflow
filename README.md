# Get Asset Values

This project is designed to find values, for a number of asset locations, from a number of spatial datasets. Currently it is setup to get values from Cloud Optimised Geotiffs (COGs) from a link to STAC items.

## Inputs

### stac_items

A list of stac items for which to get values from.

#### Example
```json
[
    "s3://lst-cogs/catalog/lst_images/2022/ESACCI-LST-L2P-LST-LNDST8-LONDON-20220710105237-fv1.00.json",
    "s3://lst-cogs/catalog/lst_images/2015/ESACCI-LST-L2P-LST-LNDST8-LONDON-20150119105810-fv1.00.json"
  ]
```

### points_json

GeoJSON list of latitudes and longitudes.

```json
{
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        -0.077,
                        51.482
                    ]
                },
                "properties": {
                    "rand_point_id": 0
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        0.295,
                        51.926
                    ]
                },
                "properties": {
                    "rand_point_id": 1
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        0.04,
                        51.286
                    ]
                },
                "properties": {
                    "rand_point_id": 2
                }
            }
        ]
    }
}
```


## Running in workflow

Send a `post` request to `https://test.eodatahub.org.uk/ades/sparkgeouser/ogc-api/processes/get-asset-values-workflow/execution` with an input similar to the below. You will need to use a token to authenticate.

```json
{
    "inputs": {
        "workspace": "sparkgeouser",
        "points_json": "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"geometry\":{\"type\":\"Point\",\"coordinates\":[-0.077,51.482]},\"properties\":{\"rand_point_id\":0}},{\"type\":\"Feature\",\"geometry\":{\"type\":\"Point\",\"coordinates\":[0.295,51.926]},\"properties\":{\"rand_point_id\":1}}]}",
        "stac_items": "[\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130419110022-fv1.00.json\",\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130428105409-fv1.00.json\",\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130428105433-fv1.00.json\"]"
    }
}
```

This will respond with a URL to poll for the results. Once that api responds with a status of 'successful'. Use the jobID to then get the results by sending a `GET` request to `https://sparkgeouser.workspaces.test.eodhp.eco-ke-staging.com/files/eodhp-test-workspaces1/processing-results/cat_{jobID}.json` (this requires an s3 authentication token).

## Running in lambda

Send a `POST` request to `https://hjbphasm1i.execute-api.eu-west-1.amazonaws.com/Prod/values` with a input like the below.

```json
{
  "stac_items":[
    "s3://lst-cogs/catalog/lst_images/2022/ESACCI-LST-L2P-LST-LNDST8-LONDON-20220710105237-fv1.00.json",
    "s3://lst-cogs/catalog/lst_images/2015/ESACCI-LST-L2P-LST-LNDST8-LONDON-20150119105810-fv1.00.json"
  ] ,
  "points_json":{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -0.077,
                    51.482
                ]
            },
            "properties": {
                "rand_point_id": 0
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    0.295,
                    51.926
                ]
            },
            "properties": {
                "rand_point_id": 1
            }
        }
    ]
},
}
```

## Running locally

You can create a fastapi endpoint by go to the `src/app` folder and running `uvicorn local_api:app --reload`. You can then send the same type of request to `http://127.0.0.1:8000` as to the lambda.