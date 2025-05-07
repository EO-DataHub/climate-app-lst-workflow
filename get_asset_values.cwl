cwlVersion: v1.2
$graph:
  - class: Workflow
    id: lst-min-max_2
    label: Land Surface Temperature (LST)
    doc: >
      The Land Surface Temperature workflow will report on observed land surface temperature observations from your assets.
    requirements:
      - class: ResourceRequirement
        coresMax: 2
        ramMax: 2048
      - class: NetworkAccess
        networkAccess: true
    inputs:
      assets:
        type: string
        doc: GeoJSON file with points data
      stac_catalog:
        type: string
        doc: STAC catalog to search
      start_date:
        type: string
        doc: start date to start the STAC search from
      end_date:
        type: string
        doc: end date for STAC search
      stac_collection:
        type: string
        doc: STAC collection to search
      stac_query:
        type: string?
        doc: 
      extra_args:
        type:
          - "null"
          - type: record
            fields: []
        doc: JSON object with additional arguments to pass to the data loader
    outputs:
      - id: asset-result
        type: Directory
        outputSource:
          - get-values/asset-result
    steps:
      get-values:
        run: "#get-asset-values"
        in:
          assets: assets
          stac_catalog: stac_catalog
          start_date: start_date
          end_date: end_date
          stac_collection: stac_collection
          stac_query: stac_query
          extra_args: extra_args
        out:
          - asset-result
  - class: CommandLineTool
    id: get-asset-values
    requirements:
        NetworkAccess:
            networkAccess: true
        DockerRequirement:
            dockerPull: public.ecr.aws/z0u8g6n1/get_asset_values:stats_06
        InitialWorkDirRequirement:
            listing:
              - entryname: output
                entry: |
                  {
                    "type": "Directory",
                    "basename": "output",
                    "listing": []
                  }
    baseCommand: main.py
    inputs:
        assets:
            type: string
            inputBinding:
                prefix: --assets=
                separate: false
                position: 4
        stac_query:
            type: string?
            inputBinding:
                prefix: --stac_query=
                separate: false
                position: 5
        stac_catalog:
            type: string
            inputBinding:
                prefix: --stac_catalog=
                separate: false
                position: 5
        start_date:
            type: string
            inputBinding:
                prefix: --start_date=
                separate: false
                position: 5
        end_date:
            type: string
            inputBinding:
                prefix: --end_date=
                separate: false
                position: 5
        stac_collection:
            type: string
            inputBinding:
                prefix: --stac_collection=
                separate: false
                position: 5
        extra_args:
            type:
              - "null"
              - type: record
                fields: []
            inputBinding:
                prefix: --extra_args=
                separate: false
                position: 6
                valueFrom: $(JSON.stringify(self))
    outputs:
        asset-result:
            type: Directory
            outputBinding:
                glob: output