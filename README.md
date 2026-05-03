# IH-Benchmark

IH-Benchmark (IHB) is a conflict-centered benchmark for evaluating instruction-hierarchy robustness in large language models. It measures whether models preserve higher-priority instructions when lower-priority inputs conflict with them, across two hierarchy surfaces and 44 constraint families.

---

## Instructions

### Setup

Create venv and install requirements:

```
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

API keys are loaded from a `.env` file:

```
cp .env.example .env
# add provider keys
```

## Running the benchmark

```
ihbenchmark --config-path ./config/config_ihb.yaml --n-threads 16
```

Results are written to `results/{RUN_ID}.csv` where `RUN_ID` is a GUID assigned at runtime.

**Options**

| Flag | Description |
|------|-------------|
| `-c / --config-path` | Path to config file (default: `./config/config_ihb.yaml`) |
| `-t / --n-threads` | Parallel requests; `0` runs single-threaded |

### Configuration

The config file specifies which models to evaluate, which prompt sets to load, and how judges are configured.

```yaml
models:
  - name: openai/gpt-5.4-2026-03-05   # litellm-style provider prefix
    pretty_name: openai/gpt-5.4
    reasoning_effort: medium           # none | low | medium | high (where supported)

prompt_sets:
  - data/ihb/prompts_system_user.json
  - data/ihb/prompts_user_tool.json

max_retries_client: 5
max_retries_judge: 2
```

Model names use LiteLLM provider-style prefixes; any provider supported by LiteLLM can be used. To evaluate additional models, uncomment the relevant entries in the config or add new ones following the same structure.

**Evaluation.** Each scenario is evaluated by a predicate DSL expression combining string matching, structural checks, tool-call inspection, language detection, and logical combinators. For constraint categories where rule compliance cannot be determined mechanically - `brand` (competitor steering and brand disparagement) and `topic` (engagement with a forbidden or required topic) — a category-scoped LLM judge is used, configured under the `judges` key in the config.

---

## Post-processing results

Two scripts convert raw run output into the format used by the visualisation layer:

```
# Extract per-model simplified CSVs from a completed run
python ./scripts/extract_simplified_results.py -r {RUN_ID}

# Merge all per-model CSVs into a single parquet file
python ./scripts/merge_simplified_results.py
```

Outputs are written to `ihbenchmark-vis/data/`. The merge script skips this step if `merged.parquet` already exists unless `--force` is passed.

An additional helper script is provided to update the terminology used in the post-processed results to exactly match any terms used in the paper:

```
python ./scripts/convert_to_paper_terminology.py
```

---

## Constructing the benchmark data

The benchmark JSON files in `data/ihb/` are included in the repository and do not need to be regenerated. If you wish to reconstruct them from source, the two preparation scripts can be run directly from the repo root:

```
python ./scripts/prepare_ihb_system_user.py
python ./scripts/prepare_ihb_user_tool.py
```

Each script writes its output (`prompts_system_user.json` / `prompts_user_tool.json`) to the current working directory.

---

## Paper data

Results from the paper are in `materials/`:

| File | Contents |
|------|----------|
| `materials/results_full_XX_of_05.parquet` | Raw results including conversation traces and per-predicate judgements across both tracks and 37 model variants (split across 5 separate parquet files) |
| `materials/results_simple.parquet` | Simplified and merged results in the same format produced by the post-processing scripts |
| `materials/results_paper.parquet` | Simplified and merged results in the same format produced by the post-processing scripts with certain columns and terms renamed to match the terminology used by the paper |

---

## License

Code is licensed under Apache 2.0; benchmark data and materials are licensed under CC BY-NC 4.0. See [`LICENSE`](LICENSE) for the full mapping.
