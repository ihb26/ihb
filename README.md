# IH-Benchmark

IH-Benchmark (IHB) is a conflict-centered benchmark for evaluating instruction-hierarchy robustness in large language models. It measures whether models preserve higher-priority instructions when lower-priority inputs conflict with them, across two hierarchy surfaces and 44 constraint families.

---

## Instructions

### Setup

Clone the `ihb` branch of this repository:

```
git clone -b ihb https://github.com/ihb26/ihb.git
```

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
    reasoning_effort: medium          # none | low | medium | high (where supported)

prompt_sets:
  - data/ihb/prompts_system_user.json
  - data/ihb/prompts_user_tool.json

max_retries_client: 5
max_retries_judge: 2
```

Model names use LiteLLM provider-style prefixes; any provider supported by LiteLLM can be used. To evaluate additional models, uncomment the relevant entries in the config or add new ones following the same structure.

**Evaluation.** Each scenario is evaluated by a predicate DSL expression combining string matching, structural checks, tool-call inspection, language detection, and logical combinators. For constraint categories where rule compliance cannot be determined mechanically a category-scoped LLM judge is used, configured under the `judges` key in the config.

---

## Post-processing results

Ensure `results/results_full.zip` has been extracted.

Regenerate the `materials/results.csv` file:

```
python ./scripts/parse_results.py -p results/ --regen --stddev --filter
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
| `results/results_full.zip` | Archive containing raw results including conversation traces and per-predicate judgements for 5 runs each across both tracks and 32 model variants (split across numerous CSV files) |
| `materials/results.csv` | Simplified and parsed results |
| `materials/results_task_completion.csv` | Task completion analysis for a stratified sample of 10,000 successful UT scenarios |
| `materials/AdditionalAnalysis.ipynb` | Jupyter notebook containing some high-level evaluation metrics and analysis |

---

## License

Code is licensed under Apache 2.0; benchmark data and materials are licensed under CC BY-NC 4.0. See [`LICENSE`](LICENSE) for the full mapping.
