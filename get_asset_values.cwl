cwlVersion: v1.2
$graph:
  - class: Workflow
    id: lst-current
    label: get asset values
    doc: get asset values
    requirements:
      NetworkAccess:
        networkAccess: true
    inputs:
      json_string:
        type: string
        doc: JSON string with points data
    outputs:
      - id: asset-result
        type: Directory
        outputSource:
          - get-values/asset-result
    steps:
      get-values:
        run: "#get-asset-values"
        in:
          json_string: json_string
        out:
          - asset-result
  - class: CommandLineTool
    id: get-asset-values
    requirements:
        NetworkAccess:
            networkAccess: true
        DockerRequirement:
            dockerPull: public.ecr.aws/z0u8g6n1/get_asset_values:csv5
    baseCommand: main.py
    inputs:
        json_string:
            type: string
            inputBinding:
                prefix: --json_string=
                separate: false
                position: 4
    outputs:
        asset-result:
            type: Directory
            outputBinding:
                glob: .