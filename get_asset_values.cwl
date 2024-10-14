cwlVersion: v1.2
$graph:
  - class: Workflow
    id: lst2
    label: get asset values
    doc: get asset values
    requirements:
      NetworkAccess:
        networkAccess: true
    inputs:
      json_file:
        type: string
        doc: JSON file with points data
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
        out:
          - asset-result
  - class: CommandLineTool
    id: get-asset-values
    requirements:
        NetworkAccess:
            networkAccess: true
        DockerRequirement:
            dockerImageId: get_asset_values:lst2 #dockerPull: public.ecr.aws/z0u8g6n1/get_asset_values:lst
    baseCommand: main.py
    inputs:
        json_file:
            type: string
            inputBinding:
                prefix: --json_file=
                separate: false
                position: 4
    outputs:
        asset-result:
            type: Directory
            outputBinding:
                glob: "./asset_output"