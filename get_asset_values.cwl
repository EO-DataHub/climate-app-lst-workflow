cwlVersion: v1.2
$graph:
  - class: Workflow
    id: lst-filter
    label: Land Surface Temperature (LST)
    doc: >
      The Land Surface Temperature workflow will report on observed land surface temperature observations from your assets.

      This workflow requires the following columns: ID, latitude, longitude
    requirements:
      NetworkAccess:
        networkAccess: true
    inputs:
      json_file:
        type: string
        doc: JSON file with points data
      stac_query:
        type: string
        doc: 
      token:
        type: string
    outputs:
      - id: asset-result
        type: Directory
        outputSource:
          - get-values/asset-result
    steps:
      get-values:
        run: "#get-asset-values"
        in:
          json_file: json_file
          stac_query: stac_query
          token: token
        out:
          - asset-result
  - class: CommandLineTool
    id: get-asset-values
    requirements:
        NetworkAccess:
            networkAccess: true
        DockerRequirement:
            dockerPull: public.ecr.aws/z0u8g6n1/get_asset_values:filter10
    baseCommand: main.py
    inputs:
        json_file:
            type: string
            inputBinding:
                prefix: --json_file=
                separate: false
                position: 4
        stac_query:
            type: string
            inputBinding:
                prefix: --stac_query=
                separate: false
                position: 5
        token:
            type: string
            inputBinding:
                prefix: --token=
                separate: false
                position: 6
    outputs:
        asset-result:
            type: Directory
            outputBinding:
                glob: .