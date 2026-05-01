# IH-Benchmark

## Instructions

### Setup

Create venv and install requirements:

```
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

Create credentials file then manually add provider API keys:

```
cp .env.example .env
```

### Running benchmark

The following command will run the _System-User_ and _User-Tool_ tracks of the IHB on a single model _ChatGPT 5.4_:

```
ihbenchmark --n-threads 16 --config-path ./config/config_ihb.yaml
```

This will create a CSV file in the _results/_ directory named `{RUN_ID}.csv` where `{RUN_ID}` is a GUID.

To run the benchmark on additional models either uncomment out the relevant lines from the config file (_./config/config_ihb.yaml_) or add additional model entries to the file.

### Extracting results

Running the following two scripts will (a) extract simplified data from the raw results file into CSV files (one file per model variant), and (b) merge the simplified data into a single parquet file. The simplified data will be placed in the _ihbenchmark-vis/data/_ directory.

```
python ./scripts/extract_simplified_results.py -r {RUN_ID}
python ./scripts/merge_simplified_results.py
```

## Paper Data

All results data referenced and discussed in the paper can be found in the _materials/_ directory, which contains the following files:

| Path | Contents |
| --- | --- |
| `materials/results_full.parquet` | Consists of the raw results, including conversation traces and DSL predicate judgements, across both tracks and 37 model variants. This file is in the same format as the results output by running the benchmark (although it has been converted from CSV to parquet to reduce the file size). |
| `materials/results_simple.parquet` | Consists of the simplified and merged results. This file is in the same format as the results output by running both the extract and merge scripts discussed above. |
