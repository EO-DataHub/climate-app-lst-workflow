# Get Asset Values

This project is designed to find values, for a number of asset locations, from a number of spatial datasets. Currently it is setup to get values from Cloud Optimised Geotiffs (COGs) from a link to STAC items. The project supports both COG and kerchunk datasets.

## Project Structure

```text
.
├── src/                    # Source code
│   ├── app/               # Application code
│   ├── tests/             # Test files
│   └── main.py            # Main entry point
├── docs/                  # Documentation
├── notebooks/             # Example notebooks
├── data/                  # Data files
└── docker_tmp5md79ns2/    # Docker related files
```

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -e .
```

## Running the Application

### Command Line Interface

You can run the application from the command line with various options:

```bash
python src/main.py --assets <geojson_string> \
                  --stac_catalog <catalog_url> \
                  --stac_collection <collection_id> \
                  --start_date <start_date> \
                  --end_date <end_date> \
                  --max_items <max_items> \
                  --expression <expression> \
                  --output_type <output_type> \
                  --variable <variable>
```

### Running in workflow

Send a `post` request to `https://eodatahub.org.uk/api/catalogue/stac/catalogs/user/catalogs/sparkgeouser/processes/lst-min-max/execution` with an input similar to the examples below. You will need to use a token to authenticate.

### Example 1: S3 Dataset with Temperature Conversion

```json
{
    "inputs": {
        "assets": "https://lst-cogs.s3.eu-west-1.amazonaws.com/test_data/uk_retail_40items_4326.geojson",
        "stac_catalog": "https://api.stac.ceda.ac.uk/",
        "start_date": "2024-07-01",
        "end_date": "2024-07-31",
        "stac_collection": "['eocis-lst-s3b-day', 'eocis-lst-s3a-day']",
        "extra_args": "{'output_name':\"{datetime_string[:-9]}_{file_name.split('_')[3].split('-')[0]}_S3{file_name.split('_')[1].split('-')[4][5]}\",'variable':'lst','unit':'°C','expression':'x - 273.15'}"
    }
}
```

### Example 2: London Dataset

```json
{
    "inputs": {
        "workspace": "sparkgeouser",
        "assets": "sparkgeouser/points.geojson",
        "stac_catalog": "https://test.eodatahub.org.uk/api/catalogue/stac/catalogs/supported-datasets/temp-sparkgeouser/processing-results/cat_c1f6f668-b2f8-11ef-b6b1-ee3aaed8a789",
        "start_date": "2022-06-01",
        "end_date": "2022-06-30",
        "stac_collection": "col_c1f6f668-b2f8-11ef-b6b1-ee3aaed8a789",
        "extra_args": "{'output_name':'{datetime_string}'}"
    }
}
```

This will respond with a URL to poll for the results. Once that api responds with a status of 'successful'. Use the jobID to then get the results by sending a `GET` request to the URL specified for the results (this requires an s3 authentication token).

### Running in lambda

Send a `POST` request to `https://hjbphasm1i.execute-api.eu-west-1.amazonaws.com/Prod/values` with a input like the below.

```json
{
  "stac_items":[
    "s3://lst-cogs/catalog/lst_images/2022/ESACCI-LST-L2P-LST-LNDST8-LONDON-20220710105237-fv1.00.json",
    "s3://lst-cogs/catalog/lst_images/2015/ESACCI-LST-L2P-LST-LNDST8-LONDON-20150119105810-fv1.00.json"
  ] ,
  "json_string":{
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
        }
    ]
}
}
```

## Additional Parameters

- `expression`: Expression to evaluate on the data (e.g., 'x - 273.15' for Kelvin to Celsius conversion)
- `output_type`: Type of output to generate (e.g., "min_max")
- `variable`: Variable to extract from the datasets (e.g., 'lst' for land surface temperature)
- `max_items`: Maximum number of STAC items to process
- `stac_query`: Additional query parameters for STAC search
- `unit`: Unit of measurement for the output values (e.g., '°C')
- `output_name`: Template for naming output files, supports string formatting with variables like `datetime_string` and `file_name`

## Dataset Support

The project supports multiple types of datasets:

- Cloud Optimised Geotiffs (COGs)
- Kerchunk datasets
- STAC catalog items

Each dataset type can be accessed through the appropriate STAC catalog URL and collection ID.
