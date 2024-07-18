cwlVersion: v1.2
$graph:
  - class: Workflow
    id: get-asset-values-workflow
    label: get asset values
    doc: get asset values
    requirements:
      NetworkAccess:
        networkAccess: true
    inputs:
      points_json:
        type: string
        doc: JSON string with points data
      stac_items:
        type: string
        doc: STAC item URLs
      latitude_key:
        type: string
        doc: Key for latitude in points JSON
      longitude_key:
        type: string
        doc: Key for longitude in points JSON
    outputs:
      - id: asset-result
        type: Directory
        outputSource:
          - get-values/asset-result
    steps:
      get-values:
        run: "#get-asset-values"
        in:
          points_json: points_json
          stac_items: stac_items
          latitude_key: latitude_key
          longitude_key: longitude_key
        out:
          - asset-result
  - class: CommandLineTool
    id: get-asset-values
    requirements:
        NetworkAccess:
            networkAccess: true
        DockerRequirement:
            dockerPull: public.ecr.aws/z0u8g6n1/get_asset_values:latest
    baseCommand: main.py
    inputs:
        points_json:
            type: string
            inputBinding:
                prefix: --points_json=
                separate: false
                position: 4
        stac_items:
            type: string
            inputBinding:
                prefix: --stac_items=
                separate: false
                position: 4
        latitude_key:
            type: string
            inputBinding:
                prefix: --latitude_key=
                separate: false
                position: 4
        longitude_key:
            type: string
            inputBinding:
                prefix: --longitude_key=
                separate: false
                position: 4
    outputs:
        asset-result:
            type: Directory
            outputBinding:
                glob: "./asset_output"