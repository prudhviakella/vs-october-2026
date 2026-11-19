# How to See Your Eval Results in MLflow — A Beginner's Guide

**VidyaSankalp · Applied GenAI Engineering** · Tutor: Prudhvi Akella

```text
  You run notebook 03
          │
          ▼
  The last chapter SAVES your scores           ← happens by itself, nothing to set up
          │
          ▼
  A file called mlflow.db appears              ← next to your notebook
  and a folder called mlruns
          │
          ▼
  You type ONE command in the terminal         ← only when you want to look
          │
          ▼
  You open a web page in your browser          ← all your results, as a nice table
```

---

## What is this, in one paragraph?

Notebook 03 checks how well our search works and gives it **scores** (numbers between 0 and 1). If you run the
notebook today, change something, and run it again tomorrow, you want to see **both** results side by side.
**MLflow** is a free tool that saves the scores of every run and shows them on a web page in your browser. It runs
on your own computer. You do not need any account.

---

## Words you will see on the screen

| Word | What it means for us |
|---|---|
| **Experiment** | A folder that holds all your results. Ours is called `vectordb-03-retrieval-eval`. |
| **Run** | One time you ran notebook 03. Run it 3 times → 3 runs. |
| **Metric** | A score. Example: `golden_pack_completeness = 0.92`. Higher is better. |
| **Parameter** | A setting that was used for that run. Example: which embedding model. |
| **Artifact** | A file saved with the run. Example: `misses.csv`, the list of questions that failed. |

That's all the vocabulary you need.

---

## Step 1 — Run notebook 03

1. First make sure notebook 02 has been run once (it puts the data into Pinecone).
2. Open `03_Evaluate_Retrieval.ipynb` and run all cells, from top to bottom.
3. Go to chapter **8 — Save the run**. Under it you should see something like:

```text
✅ Saved to MLflow as run_20261117_142621
```

✅ If you see this, your results are saved. `run_20261117_142621` is just the date and time of the run.

Look in your project folder (the left side panel in PyCharm). Two new things appeared next to the notebook:

```text
your-project-folder
├── 03_Evaluate_Retrieval.ipynb
├── mlflow.db        ← NEW: the scores
├── mlruns           ← NEW: the saved files
└── docs
```

> Don't delete, move or rename these two. MLflow needs them to show your results.

---

## Step 2 — Open the terminal in PyCharm

The terminal is a window where you type commands.

- **Windows:** press **Alt + F12**
- **Mac:** press **Option + F12**

Or use the menu: **View → Tool Windows → Terminal**.

A panel opens at the bottom of PyCharm with a blinking cursor. Usually it already starts **inside your project
folder** and with your **virtual environment** switched on — you will often see `(.venv)` at the start of the line:

```text
(.venv) C:\Users\you\vectordb-course>          ← Windows
(.venv) you@MacBook vectordb-course %          ← Mac
```

If you see `(.venv)` and your project folder name, **skip to Step 4**.

---

## Step 3 — Only if needed: go to the right folder and switch on the environment

Do this only if the terminal did **not** show your project folder or `(.venv)`.

**Find your folder's path:** in PyCharm's left panel, right-click the notebook `03_Evaluate_Retrieval.ipynb` →
**Copy Path/Reference…** → **Absolute Path**. That copies something like
`C:\Users\you\vectordb-course\03_Evaluate_Retrieval.ipynb`. The folder is everything **before** the file name.

**Windows** — type these, pressing Enter after each line (use your own folder path):

```text
cd C:\Users\you\vectordb-course
.venv\Scripts\activate
```

**Mac** — type these, pressing Enter after each line (use your own folder path):

```text
cd /Users/you/vectordb-course
source .venv/bin/activate
```

✅ The line now starts with `(.venv)`.

> If your project's environment folder has a different name (for example `venv` without the dot), use that name
> instead of `.venv`.

---

## Step 4 — Start the MLflow screen

Type this one command and press Enter. It is the **same on Windows and Mac**:

```text
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001
```

What the parts mean — you don't need to change any of them:

| Part | Meaning |
|---|---|
| `mlflow ui` | start the MLflow web page |
| `--backend-store-uri sqlite:///mlflow.db` | read the scores from the `mlflow.db` file in this folder |
| `--port 5001` | the "door number" the web page uses on your computer |

After a few seconds the terminal shows lines ending with something like:

```text
INFO:     Uvicorn running on http://127.0.0.1:5001 (Press CTRL+C to quit)
```

You will also see other lines and maybe some warnings above it — that's normal, ignore them.

✅ MLflow is running. **Leave this terminal open** — if you close it, the web page stops working.

---

## Step 5 — Open the web page

Open your browser (Chrome, Edge, Safari…) and type this in the address bar:

```text
http://127.0.0.1:5001
```

`127.0.0.1` means "this computer". Nobody else can see this page.

You should see the MLflow home page.

1. Click **Experiments** (on the left or at the top).
2. Click **`vectordb-03-retrieval-eval`**.
3. You now see a **table of runs** — one row for each time you ran notebook 03, newest at the top.

> The screen may look a little different depending on your MLflow version. Look for the same words:
> Experiments, Runs, Compare, Artifacts.

---

## Step 6 — Look at one run

Click the **name of a run** (it looks like `run_20261117_134726` — the date and time you ran it).

**Overview** — the main page of the run:

- **Parameters**: the settings used, like `embed_model = text-embedding-3-small`.
- **Metrics**: all the scores. The most important one is **`golden_pack_completeness`** — how often the search gave
  the AI everything it needed. Close to 1.0 is good.

**Artifacts** — the files saved with the run (click the Artifacts tab):

| File | What's inside |
|---|---|
| `per_question.json` | **every question** that was tested, with `passed` = 1 (good) or 0 (failed) |
| `misses.csv` | **only the failed questions** — the ones to work on. Click it, then the download button to open it in Excel |

---

## Step 7 — Compare two runs

This is the main reason we use MLflow.

1. Run notebook 03 **once** as it is.
2. Fix one mistake from chapter 6 of the notebook — for example, add a missing word to a glossary term's
   **synonyms** in `kb_feed_ecom.xlsx`. Save the Excel file.
3. Run notebook 02 again (so Pinecone gets the fixed text), then run notebook 03 **again**, all cells.
4. Go back to the MLflow page and **refresh** it (F5 on Windows, Cmd + R on Mac). You now see **2 runs**.
5. Tick the **checkbox** next to both runs.
6. Click **Compare**.

You see both runs side by side. Look at `golden_pack_completeness` and `glossary_in_top_3` — did they go up? That
tells you exactly what your fix did.

---

## Step 8 — Stop MLflow when you are done

Click inside the terminal where MLflow is running and press:

- **Windows:** **Ctrl + C**
- **Mac:** **Control + C**

The web page stops working — that's expected. Your results are **not** deleted; they stay in `mlflow.db`. Next time,
just do Step 4 and Step 5 again.

---

## If something goes wrong

**"mlflow is not recognized" (Windows) or "command not found: mlflow" (Mac)**
The environment is not switched on, or MLflow isn't installed. Do Step 3, then run:

```text
pip install mlflow
```

and try Step 4 again.

**The page opens but shows no runs, or no `vectordb-03-retrieval-eval`**
MLflow was started in the wrong folder. It then creates a new, **empty** `mlflow.db` there. Stop it (Step 8), go to
your notebook's folder (Step 3), and start it again (Step 4). Delete the extra empty `mlflow.db` it created in the
wrong folder.

**"Address already in use" or the port is busy**
Another program is using door number 5001. Use a different number, both in the command and in the browser:

```text
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5002
```

then open `http://127.0.0.1:5002`.

**The browser says "This site can't be reached"**
MLflow is not running. Check the terminal: is it still open, and did you see the `Uvicorn running…` line? Wait a few
seconds and refresh the page.

**Chapter 8 in the notebook shows an error**
Read the last line of the red error message. Most often a cell above it was skipped — run the notebook again from
the top.

---

## Start completely fresh (optional)

To remove all saved runs and begin again:

1. Stop MLflow (Step 8).
2. In PyCharm's left panel, right-click **`mlflow.db`** → **Delete**.
3. Right-click the **`mlruns`** folder → **Delete**.
4. Run notebook 03 again — both come back, with only the new run.

To remove just **one** run: on the MLflow page tick that run → **Delete**.

---

## Quick checklist

```text
☐ notebook 02 run once
☐ notebook 03 run, chapter 8 says "✅ Saved to MLflow as run_…"
☐ terminal open in the project folder, line starts with (.venv)
☐ mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001
☐ browser: http://127.0.0.1:5001 → Experiments → vectordb-03-retrieval-eval
☐ done? Ctrl + C (Windows) / Control + C (Mac) in the terminal
```

---

## Good to know

- MLflow **does not calculate** anything. Notebook 03 calculates the scores; MLflow only **saves and shows** them.
- Your runs stay **on your computer**. Other people can't see them.
- Later in the course we can save the same runs to **MLflow on AWS (SageMaker)** — then only one line in chapter 8
  changes.
