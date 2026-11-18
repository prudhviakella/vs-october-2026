# MLflow for Notebook 03 — Publishing the Eval Runs

**VidyaSankalp · Applied GenAI Engineering** · Tutor: Prudhvi Akella

```text
03_Evaluate_Retrieval.ipynb
        │  Chapter 15: mlflow.start_run()
        ▼
┌───────────────────────────────────────────────────────────────┐
│  one RUN                                                      │
│   params    what was tested    model · index · top_k · …      │
│   metrics   the averages       pack completeness · Recall@3 … │
│   table     every question     per_question.json (786 rows)   │
│   files     misses.csv · run CSV · the answer key             │
└───────────────────────────────────────────────────────────────┘
        │  written to two places next to the notebook
        ▼
  mlflow.db   (params, metrics, tags)     mlruns/   (files and the table)
        │
        ▼
  mlflow ui  ──►  http://127.0.0.1:5001   runs side by side · Compare · Artifacts
```

No account and no server are needed to **publish**. You only start `mlflow ui` when you want to **look**.

---

## 1. What MLflow is used for here

Every time you run notebook 03, it scores retrieval and publishes the result as one **run**. MLflow keeps all runs
together, so you can compare them: before and after a fix in the knowledge base, `EXAMPLES_IN_PACK = 2` vs `1`,
or one embedding model vs another.

| MLflow word | Meaning here | Example |
|---|---|---|
| **experiment** | one project: all eval runs of this knowledge base | `vectordb-03-retrieval-eval` |
| **run** | one execution of notebook 03 | `run_20261117_134726` |
| **param** | a setting that was used | `embed_model = text-embedding-3-small` |
| **metric** | a number the run produced | `golden_pack_completeness = 0.92` |
| **artifact** | a file attached to the run | `misses.csv` |
| **tag** | a short label shown in the run list | `targets_met = 7 of 9` |

---

## 2. Install (once)

MLflow is installed by the first cell of notebook 03 (`%pip install … mlflow`). To install it from the terminal
instead, open the **PyCharm Terminal**.

**Windows**

```text
cd path\to\your\vectordb-folder
.venv\Scripts\activate
pip install mlflow
mlflow --version
```

**Mac**

```text
cd path/to/your/vectordb-folder
source .venv/bin/activate
pip install mlflow
mlflow --version
```

`mlflow --version` should print a version number (tested with 3.18).

---

## 3. Publish a run

1. Run notebook 02 once (the records must be in Pinecone).
2. Run notebook 03 from top to bottom.
3. Chapter 15 prints:

```text
Published run 5f6d3343d0594a5ab6cdc544ddbe2534 to experiment 'vectordb-03-retrieval-eval'
Questions in the table: 786
```

Two new things appear next to the notebook:

```text
vectordb-folder/
├── 03_Evaluate_Retrieval.ipynb
├── mlflow.db          ← params, metrics, tags of every run
├── mlruns/            ← the files of every run (misses.csv, per_question.json, …)
├── eval_runs/         ← the notebook's own CSVs (chapter 12–13)
└── docs/
    └── ground_truth_ecom.xlsx
```

---

## 4. Open the MLflow screen

The command must run **in the same folder as `mlflow.db`**. It keeps running; stop it with **Ctrl + C**.

**Windows**

```text
cd path\to\your\vectordb-folder
.venv\Scripts\activate
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001
```

**Mac**

```text
cd path/to/your/vectordb-folder
source .venv/bin/activate
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001
```

Open **http://127.0.0.1:5001** in the browser.

We use port **5001** because on a Mac port 5000 is often taken by AirPlay Receiver.

When you are done:

```text
Ctrl + C          (in the terminal where mlflow ui is running)
cd ..             (back to where you started, if you need to)
```

---

## 5. What to look at

| Where | What you see | Use it to |
|---|---|---|
| **Experiments → `vectordb-03-retrieval-eval`** | one row per run; metrics as columns | spot the best and worst runs at a glance |
| **Columns** button | choose which metrics to show | keep `golden_pack_completeness`, `glossary_recall_at_3`, `targets_met` visible |
| tick **two runs → Compare** | every param and metric side by side | see what a change did |
| a run → **Overview** | its params, metrics and tags | check exactly what was tested |
| a run → **Artifacts → `per_question.json`** | every question: passed, missing records, top 3 | find which questions failed |
| a run → **Artifacts → `misses.csv`** | only the misses | download and work through them (notebook 03, chapter 12) |

### The metrics

| Metric | From chapter |
|---|---|
| `golden_pack_completeness` | 9 — the headline number |
| `golden_example_hit` | 9 |
| `glossary_recall_at_3`, `glossary_hit_at_1`, `glossary_mrr` | 7 |
| `examples_recall_at_3`, `examples_hit_at_1`, `examples_mrr` | 7 |
| `joins_recall_at_3`, `joins_hit_at_1`, `joins_mrr` | 7 |
| `schema_real_wording_recall_at_3` | 7 |
| `glossary_keyword_recall_at_3`, `examples_keyword_recall_at_3`, `joins_keyword_recall_at_3` | 8 — the baseline |
| `cant_answer_card_found_by_search` | 10 |
| `targets_met` | 14 |

---

## 6. A first comparison (5 minutes)

1. Run notebook 03 as it is → run **A**.
2. In chapter 6 set `EXAMPLES_IN_PACK = 1`, run the notebook again → run **B**.
3. In MLflow tick runs A and B → **Compare**.
4. Which metrics moved? (`golden_example_hit` should; the glossary and schema metrics should not.)
5. Set `EXAMPLES_IN_PACK` back to `2`.

The same steps work for any change: a synonym added to `kb_feed_ecom.xlsx` (reload in notebook 02 first), a
different `top_k`, or a different embedding model.

---

## 7. Clean up

| To | Do |
|---|---|
| remove one run | in the run list tick it → **Delete** |
| start completely fresh | stop `mlflow ui`, then delete `mlflow.db` and the `mlruns` folder |

**Windows**

```text
cd path\to\your\vectordb-folder
del mlflow.db
rmdir /s /q mlruns
```

**Mac**

```text
cd path/to/your/vectordb-folder
rm mlflow.db
rm -rf mlruns
```

---

## 8. When something goes wrong

| You see | Why | Fix |
|---|---|---|
| `mlflow: command not found` / `'mlflow' is not recognized` | the virtual environment is not active | run the `activate` line from section 4 first |
| the screen opens but shows **no runs** | `mlflow ui` was started in a different folder, so it made a new empty `mlflow.db` | stop it, `cd` into the notebook's folder, start it again |
| `Address already in use` / port error | something else uses port 5001 | use another port: `--port 5002` |
| the page doesn't load | `mlflow ui` is not running, or still starting | check the terminal; wait a few seconds; reload |
| `per_question.json` is missing from Artifacts | the run stopped before step 3 of chapter 15 | read the error in the notebook, fix it, run chapter 15 again |
| a Chapter 15 error about a metric name | a name with characters MLflow doesn't allow | `metric_name()` cleans names — don't log metrics without it |

---

## 9. Later: SageMaker serverless MLflow

To publish to MLflow on AWS instead of the local file, only one line in chapter 15 changes:

```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")          # now: local file
mlflow.set_tracking_uri("<your MLflow App ARN>")         # later: SageMaker AI serverless MLflow
```

That also needs the `sagemaker-mlflow` package and AWS credentials with access to the MLflow App. Everything else
in the notebook stays the same. Check that serverless MLflow is available in your AWS region before planning on it.

---

## What this does NOT do

- It does not **score** anything. Notebook 03 computes every number; MLflow only stores and shows them.
- It does not **share** runs with other people. The runs live on your computer. To share, use SageMaker MLflow
  (section 9) or send the `misses.csv` / `per_question.json` files.
- It does not evaluate the **agent**. That comes with Agent Version 3 and AgentCore batch evaluations.
