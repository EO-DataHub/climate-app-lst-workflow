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

A json list of latitudes and longitudes.

```text
"[{ \"rand_point_id\": 0, \"longitude\": -0.077, \"latitude\": 51.482},{ \"rand_point_id\": 1, \"longitude\": 0.295, \"latitude\": 51.926},{ \"rand_point_id\": 2, \"longitude\": 0.04, \"latitude\": 51.286},{ \"rand_point_id\": 3, \"longitude\": -0.247, \"latitude\": 51.765},{ \"rand_point_id\": 4, \"longitude\": 0.478, \"latitude\": 51.732},{ \"rand_point_id\": 5, \"longitude\": 0.449, \"latitude\": 51.058},{ \"rand_point_id\": 6, \"longitude\": 0.232, \"latitude\": 51.865},{ \"rand_point_id\": 7, \"longitude\": 0.278, \"latitude\": 51.074},{ \"rand_point_id\": 8, \"longitude\": 0.302, \"latitude\": 51.471},{ \"rand_point_id\": 9, \"longitude\": 0.222, \"latitude\": 51.557}]"
```

### latitude_key & longitude_key

By default 'latitude' and 'longitude' are the keys in the points_json for latitude and longitude. If the keys are different then these need to be added.

## Running in workflow

Send a `post` request to `https://test.eodatahub.org.uk/ades/eric/ogc-api/processes/get-asset-values-workflow/execution` with an input similar to the below. You will need to use a username and password to authenticate.

```json
{
    "inputs": {
        "workspace": "ddowding",
        "latitude_key": "latitude",
        "longitude_key": "longitude",
        "points_json": "[{ \"rand_point_id\": 0, \"longitude\": -0.077, \"latitude\": 51.482},{ \"rand_point_id\": 1, \"longitude\": 0.295, \"latitude\": 51.926},{ \"rand_point_id\": 2, \"longitude\": 0.04, \"latitude\": 51.286},{ \"rand_point_id\": 3, \"longitude\": -0.247, \"latitude\": 51.765},{ \"rand_point_id\": 4, \"longitude\": 0.478, \"latitude\": 51.732},{ \"rand_point_id\": 5, \"longitude\": 0.449, \"latitude\": 51.058},{ \"rand_point_id\": 6, \"longitude\": 0.232, \"latitude\": 51.865},{ \"rand_point_id\": 7, \"longitude\": 0.278, \"latitude\": 51.074},{ \"rand_point_id\": 8, \"longitude\": 0.302, \"latitude\": 51.471},{ \"rand_point_id\": 9, \"longitude\": 0.222, \"latitude\": 51.557}]",
        "stac_items": "[\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130419110022-fv1.00.json\",\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130428105409-fv1.00.json\",\"s3://lst-cogs/catalog/lst_images/2013/ESACCI-LST-L2P-LST-LNDST8-LONDON-20130428105433-fv1.00.json\"]"
    }
}
```

This will respond with a URL to poll for the results. Once that api responds with a status of 'successful'. Use the jobID to then get the results by sending a `GET` request to `https://ddowding.workspaces.test.eodhp.eco-ke-staging.com/files/eodhp-test-workspaces1/processing-results/cat_{jobID}.json` (this requires an authentication token).

## Running in lambda

Send a `POST` request to `https://hjbphasm1i.execute-api.eu-west-1.amazonaws.com/Prod/values` with a input like the below.

```json
{
  "stac_items":[
    "s3://lst-cogs/catalog/lst_images/2022/ESACCI-LST-L2P-LST-LNDST8-LONDON-20220710105237-fv1.00.json",
    "s3://lst-cogs/catalog/lst_images/2015/ESACCI-LST-L2P-LST-LNDST8-LONDON-20150119105810-fv1.00.json"
  ] ,
  "points_json": "[{ \"rand_point_id\": 0, \"longitude\": -0.077, \"latitude\": 51.482},{ \"rand_point_id\": 1, \"longitude\": 0.295, \"latitude\": 51.926},{ \"rand_point_id\": 2, \"longitude\": 0.04, \"latitude\": 51.286},{ \"rand_point_id\": 3, \"longitude\": -0.247, \"latitude\": 51.765},{ \"rand_point_id\": 4, \"longitude\": 0.478, \"latitude\": 51.732},{ \"rand_point_id\": 5, \"longitude\": 0.449, \"latitude\": 51.058},{ \"rand_point_id\": 6, \"longitude\": 0.232, \"latitude\": 51.865},{ \"rand_point_id\": 7, \"longitude\": 0.278, \"latitude\": 51.074},{ \"rand_point_id\": 8, \"longitude\": 0.302, \"latitude\": 51.471},{ \"rand_point_id\": 9, \"longitude\": 0.222, \"latitude\": 51.557}]",
  "latitude_key": "latitude",
  "longitude_key": "longitude"
}
```
