"""
make_ground_truth.py — builds ground_truth_ecom.xlsx, the answer key for notebook 03.

    kb_feed_ecom.xlsx ──► record ids (same rules as notebook 02) ──┐
    golden.py + coverage.py (hand-written) ───────────────────────┼──► checks ──► ground_truth_ecom.xlsx
    answers_questions (workbook, not embedded) ───────────────────┘

    sheets:  README · golden (49) · glossary_questions (66) · example_questions (61) · join_questions (16)
             · languages (12) · schema_questions (582) · coverage · summary

Checks (the script stops if one fails):
    1. every id in the answer key exists among the 337 records notebook 02 loads
    2. no golden question is a copy of an embedded example question / paraphrase, or of an answers_questions entry
    3. every language row points to a golden question
    4. every glossary term, SQL example and join has exactly one coverage question
    5. a glossary question never contains its own term or synonyms; an example question never copies its own
       question or paraphrases (word overlap above 60% is flagged for review)

Does NOT call any API or score anything — it only writes the answer key.
"""
import re
from collections import Counter

import openpyxl
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from coverage import EXAMPLE_Q, GLOSSARY_Q, JOIN_Q
from golden import GOLDEN, LANGUAGES

KB = "../new_kb/kb_feed_ecom.xlsx"          # the workbook Prudhvi sent
OUT = "ground_truth_ecom.xlsx"

wb_in = openpyxl.load_workbook(KB, read_only=True)


def read_sheet(name):
    rows = wb_in[name].iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, r)) for r in rows if any(v is not None for v in r)]


def as_list(cell):
    return [p.strip() for p in str(cell).split(";") if p.strip()] if cell else []


def is_yes(v):
    return str(v).strip().lower() in ("y", "yes", "true")


SHEETS = {n: read_sheet(n) for n in ["nlq_table", "nlq_column", "nlq_join", "glossary", "nlq_examples", "capability_card"]}

# ── STEP 1: the 337 record ids, built exactly as notebook 02 builds them ─────────────────────────
ids = set()
for r in SHEETS["nlq_table"]:
    ids.add(f"table::{r['table']}")
for r in SHEETS["nlq_column"]:
    if not is_yes(r["embed_exempt"]):
        ids.add(f"column::{r['table']}.{r['column']}")
for r in SHEETS["nlq_join"]:
    ids.add(f"join::{r['left_table']}->{r['right_table']}::{r['join_on']}")
for r in SHEETS["glossary"]:
    ids.add(f"glossary::{r['term']}")
for n, _ in enumerate(SHEETS["nlq_examples"], 1):
    ids.add(f"nlq_examples::{n}")
for n, _ in enumerate(SHEETS["capability_card"], 1):
    ids.add(f"capability_card::{n}")
assert len(ids) == 337, len(ids)

# ── STEP 2: check the golden set ─────────────────────────────────────────────────────────────────
embedded_questions = set()
for r in SHEETS["nlq_examples"]:
    embedded_questions.add(r["question"].strip().lower())
    embedded_questions.update(p.lower() for p in as_list(r["paraphrases"]))
answer_key_questions = set()
for tab in ("nlq_table", "nlq_column"):
    for r in SHEETS[tab]:
        answer_key_questions.update(q.lower() for q in as_list(r["answers_questions"]))

problems = []
for qid, q, typ, must, helpful, ex, limits, *_ in GOLDEN:
    for i in must + helpful + ex + limits:
        if i not in ids:
            problems.append(f"{qid}: unknown id {i}")
    if q.strip().lower() in embedded_questions | answer_key_questions:
        problems.append(f"{qid}: copied from the workbook")
golden_ids = {g[0] for g in GOLDEN}
problems += [f"language row for unknown {qid}" for qid, *_ in LANGUAGES if qid not in golden_ids]

def words(text):
    return set(re.findall(r"[a-z0-9%]+", text.lower()))


def contains(phrase, text):
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9])", text.lower()) is not None


# coverage: one question per glossary term / example / join
glossary_rows = {r["term"]: r for r in SHEETS["glossary"]}
problems += [f"glossary term without a question: {t}" for t in glossary_rows if t not in GLOSSARY_Q]
problems += [f"question for unknown term: {t}" for t in GLOSSARY_Q if t not in glossary_rows]
for term, q in GLOSSARY_Q.items():
    for w in [term] + as_list(glossary_rows.get(term, {}).get("synonyms")):
        if contains(w, q):
            problems.append(f"glossary question for {term} contains '{w}'")
problems += [f"example without a question: {n}" for n in range(1, len(SHEETS["nlq_examples"]) + 1) if n not in EXAMPLE_Q]
example_flags = {}
for n, q in EXAMPLE_Q.items():
    r = SHEETS["nlq_examples"][n - 1]
    own = [r["question"]] + as_list(r["paraphrases"])
    if q.strip().lower() in (o.lower() for o in own):
        problems.append(f"example {n}: copies its own text")
    overlap = max(len(words(q) & words(o)) / len(words(q) | words(o)) for o in own)
    example_flags[n] = round(overlap, 2)
join_ids = {i for i in ids if i.startswith("join::")}
problems += [f"join without a question: {j}" for j in join_ids if j not in JOIN_Q]
problems += [f"unknown join id: {j}" for j in JOIN_Q if j not in join_ids]
assert not problems, problems

# Words a golden question shares with the embedded text: glossary terms / synonyms and column names.
glossary_words = {}
for r in SHEETS["glossary"]:
    for w in [r["term"]] + as_list(r["synonyms"]):
        glossary_words[w.lower()] = r["term"]
column_words = {r["column"].replace("_", " ").lower(): f"{r['table']}.{r['column']}" for r in SHEETS["nlq_column"]}


def shared_words(question):
    ql = question.lower()
    found = []
    for w, term in glossary_words.items():
        if len(w) > 2 and re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", ql):
            found.append(f"'{w}' → glossary {term}")
    for w, col in column_words.items():
        if " " in w and re.search(rf"\b{re.escape(w)}\b", ql):
            found.append(f"'{w}' → column {col}")
    return "\n".join(sorted(set(found)))


# ── STEP 3: schema_questions from answers_questions (claim A) ────────────────────────────────────
schema_rows = []
seen = {}
for tab in ("nlq_column", "nlq_table"):
    for r in SHEETS[tab]:
        if tab == "nlq_column" and is_yes(r["embed_exempt"]):
            continue
        if tab == "nlq_column":
            right = f"column::{r['table']}.{r['column']}"
            names = [r["column"].replace("_", " ").lower()] + [s.lower() for s in as_list(r["analyst_synonyms"])]
        else:
            right = f"table::{r['table']}"
            names = [r["table"].split(".")[1].replace("_", " ").lower()] + [s.lower() for s in as_list(r["analyst_synonyms"])]
        for q in as_list(r["answers_questions"]):
            note = ""
            right_ids = [right]
            # "How many orders are there?" is about the table, not the id column it was attached to
            m = re.fullmatch(r"how many (.+) are there\?", q.lower())
            if tab == "nlq_column" and m:
                right_ids = [f"table::{r['table']}"]
                note = f"moved: was attached to {right}; it asks about the whole table"
            key = q.lower()
            if key in seen:                       # same question under two records → both are right
                seen[key][3].extend(i for i in right_ids if i not in seen[key][3])
                seen[key][6] = "asked under two records — both count as right"
                continue
            named = any(n and n in q.lower() for n in names)
            row = [None, tab, q, right_ids, "Y" if named else "N",
                   "easy — names the record" if named else "real wording", note]
            seen[key] = row
            schema_rows.append(row)
for n, row in enumerate(schema_rows, 1):
    row[0] = f"S{n:04d}"

# ── STEP 4: write the workbook ───────────────────────────────────────────────────────────────────
FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
REVIEW_FILL = PatternFill("solid", fgColor="FFF2CC")
TYPE_FILL = {"jargon": "DDEBF7", "plain": "E2EFDA", "two terms": "FCE4D6", "joins": "EDE2F6",
             "rules": "FFF2CC", "can't answer": "F8CBAD", "out of scope": "D9D9D9"}
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

out = openpyxl.Workbook()


def header(ws, cols, widths):
    for c, (name, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=1, column=c, value=name)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.freeze_panes = "C2"
    ws.row_dimensions[1].height = 32


def body(ws, r, values, fill=None):
    for c, v in enumerate(values, 1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = Font(name=FONT, size=10)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = BORDER
        if fill:
            cell.fill = fill


lines = lambda xs: "\n".join(xs)

# golden ---------------------------------------------------------------------------------------
ws = out.active
ws.title = "golden"
cols = ["qid", "question", "type", "must_find (grade 2)", "helpful (grade 1)", "tables (grade 1, auto)", "example_ok (any one)",
        "limits (capability card)", "expected behaviour", "assumption to state", "why it's a good test",
        "words shared with the embedded text (auto)", "REVIEW: ok / change"]
header(ws, cols, [6, 40, 11, 44, 36, 28, 16, 16, 18, 30, 38, 34, 18])


def tables_of(must):
    """column::ecom.orders.total_amount -> table::ecom.orders  (the table each must-find column lives in)."""
    found = []
    for i in must:
        if i.startswith("column::"):
            t = "table::" + i[len("column::"):].rsplit(".", 1)[0]
            if t not in found:
                found.append(t)
    return found


for r, (qid, q, typ, must, helpful, ex, limits, beh, assume, why) in enumerate(GOLDEN, 2):
    body(ws, r, [qid, q, typ, lines(must), lines(helpful), lines(tables_of(must)), lines(ex), lines(limits), beh, assume,
                 why, shared_words(q), None])
    ws.cell(row=r, column=3).fill = PatternFill("solid", fgColor=TYPE_FILL[typ])
    ws.cell(row=r, column=6).fill = PatternFill("solid", fgColor="F2F2F2")
    ws.cell(row=r, column=13).fill = REVIEW_FILL
ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(GOLDEN) + 1}"

# glossary_questions -------------------------------------------------------------------------
def simple_sheet(title, cols, widths, rows, review_col):
    w = out.create_sheet(title)
    header(w, cols, widths)
    for r, values in enumerate(rows, 2):
        body(w, r, values)
        w.cell(row=r, column=review_col).fill = REVIEW_FILL
    w.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(rows) + 1}"
    return w


rows = []
for n, (term, q) in enumerate(GLOSSARY_Q.items(), 1):
    g = glossary_rows[term]
    rows.append([f"T{n:02d}", q, f"glossary::{term}", lines(f"column::{c}" for c in as_list(g["maps_to"])),
                 g["category"], str(g["meaning"])[:160], None])
simple_sheet("glossary_questions",
             ["tid", "question (plain words — no term, no synonym)", "right_id", "helpful: maps_to columns (grade 1)",
              "category", "meaning (from the workbook)", "REVIEW: ok / change"],
             [6, 46, 30, 40, 10, 50, 18], rows, 7)

rows = []
for n, q in EXAMPLE_Q.items():
    r = SHEETS["nlq_examples"][n - 1]
    rows.append([f"E{n:02d}", q, f"nlq_examples::{n}", r["question"], r["paraphrases"], example_flags[n],
                 "check: close to the original" if example_flags[n] > 0.6 else "", None])
w = simple_sheet("example_questions",
                 ["eid", "question (reworded)", "right_id", "original question (embedded)", "paraphrases (embedded)",
                  "word overlap with the original", "flag", "REVIEW: ok / change"],
                 [6, 46, 18, 40, 40, 12, 22, 18], rows, 8)
for r in range(2, len(rows) + 2):
    w.cell(row=r, column=6).number_format = "0%"

rows = []
join_rows = {f"join::{r['left_table']}->{r['right_table']}::{r['join_on']}": r for r in SHEETS["nlq_join"]}
for n, (jid, q) in enumerate(JOIN_Q.items(), 1):
    jr = join_rows[jid]
    rows.append([f"J{n:02d}", q, jid, jr["cardinality"], jr["description"], None])
simple_sheet("join_questions",
             ["jid", "question (needs this join)", "right_id", "cardinality", "join description (from the workbook)", "REVIEW: ok / change"],
             [6, 46, 50, 12, 50, 18], rows, 6)

# languages ------------------------------------------------------------------------------------
wl = out.create_sheet("languages")
cols = ["qid", "language", "question", "English original", "must_find", "REVIEW: translation ok?"]
header(wl, cols, [6, 11, 48, 44, 44, 20])
gmap = {g[0]: g for g in GOLDEN}
for r, (qid, lang, q) in enumerate(LANGUAGES, 2):
    body(wl, r, [qid, lang, q, gmap[qid][1], lines(gmap[qid][3]), None])
    wl.cell(row=r, column=6).fill = REVIEW_FILL
wl.auto_filter.ref = f"A1:F{len(LANGUAGES) + 1}"

# schema_questions -----------------------------------------------------------------------------
wsq = out.create_sheet("schema_questions")
cols = ["sid", "source tab", "question (from answers_questions)", "right_ids", "names the record? (Y/N)", "tier", "note"]
header(wsq, cols, [8, 13, 52, 44, 12, 22, 44])
for r, row in enumerate(schema_rows, 2):
    row = row[:3] + [lines(row[3])] + row[4:]
    body(wsq, r, row)
wsq.auto_filter.ref = f"A1:G{len(schema_rows) + 1}"

# coverage: which records are the right answer of at least one test question -----------------
covered = Counter()
for g in GOLDEN:
    for i in g[3] + g[5] + g[6]:          # must_find + example_ok + limits
        covered[i] += 1
for t in GLOSSARY_Q:
    covered[f"glossary::{t}"] += 1
for n in EXAMPLE_Q:
    covered[f"nlq_examples::{n}"] += 1
for j in JOIN_Q:
    covered[j] += 1
for row in schema_rows:
    for i in row[3]:
        covered[i] += 1
cv = out.create_sheet("coverage")
header(cv, ["record type", "records in 02", "with at least one test question", "not covered"], [18, 14, 18, 70])
kinds = ["table", "column", "join", "glossary", "nlq_examples", "capability_card"]
for r, k in enumerate(kinds, 2):
    mine = sorted(i for i in ids if i.startswith(k + "::"))
    missing = [i for i in mine if not covered[i]]
    body(cv, r, [k, len(mine), len(mine) - len(missing), lines(missing) or "—"])
body(cv, len(kinds) + 2, ["total", f"=SUM(B2:B{len(kinds) + 1})", f"=SUM(C2:C{len(kinds) + 1})", ""])
body(cv, len(kinds) + 4, ["Computed by make_ground_truth.py from all question sheets (a record counts as covered when it is "
                          "the right answer — must_find, example_ok, limits or right_id — of at least one question).", None, None, None])

# summary (formulas) ---------------------------------------------------------------------------
sm = out.create_sheet("summary")
header(sm, ["What", "Count", "How it is counted"], [46, 10, 60])
n_g, n_l, n_s = len(GOLDEN) + 1, len(LANGUAGES) + 1, len(schema_rows) + 1
summary = [
    ("Golden questions", f"=COUNTA(golden!A2:A{n_g})", "rows in golden"),
] + [(f"  type: {t}", f'=COUNTIF(golden!C2:C{n_g},"{t}")', "golden rows of this type") for t in TYPE_FILL] + [
    ("  expected to refuse", f'=COUNTIF(golden!I2:I{n_g},"refuse")', "the agent should say it can't answer"),
    ("  must state an assumption", f'=COUNTIF(golden!I2:I{n_g},"answer + state assumption")', "dates like 'last month', 'right now'"),
    ("  reviewed so far", f'=COUNTA(golden!M2:M{n_g})', "rows with something in the REVIEW column"),
    ("Glossary questions", f"=COUNTA(glossary_questions!A2:A{len(GLOSSARY_Q) + 1})", "one per glossary term, plain words"),
    ("Example questions", f"=COUNTA(example_questions!A2:A{len(EXAMPLE_Q) + 1})", "one per SQL example, reworded"),
    ("Join questions", f"=COUNTA(join_questions!A2:A{len(JOIN_Q) + 1})", "one per join"),
    ("Language questions", f"=COUNTA(languages!A2:A{n_l})", "Telugu + Hinglish versions"),
    ("Schema questions (claim A)", f"=COUNTA(schema_questions!A2:A{n_s})", "from answers_questions — not embedded in 02"),
    ("  that name the record (easy)", f'=COUNTIF(schema_questions!E2:E{n_s},"Y")', "the question contains the column/table name or a synonym"),
    ("  real wording", f'=COUNTIF(schema_questions!E2:E{n_s},"N")', ""),
    ("  share that name the record", f"=B{len(TYPE_FILL) + 11}/B{len(TYPE_FILL) + 10}", "if this is high, a high score proves little"),
]
for r, (what, f, how) in enumerate(summary, 2):
    body(sm, r, [what, f, how])
sm.cell(row=len(summary) + 1, column=2).number_format = "0%"

# README ---------------------------------------------------------------------------------------
rd = out.create_sheet("README", 0)
rd.column_dimensions["A"].width = 120
text = [
    ("Ground truth for notebook 03 — the answer key", True),
    ("A test question + the record ids it should find. Notebook 03 runs each question through the agent's lookups and checks which ids came back.", False),
    ("", False),
    ("THE ONE RULE", True),
    ("A test question must not be text we embedded in 02. If it is, the test is an open-book exam. The script checks that no golden question copies an example question, a paraphrase or an answers_questions entry.", False),
    ("Business words such as GMV, AOV, OTD are allowed: users really type them. Column 'words shared with the embedded text' shows them, so you can see how hard each question is.", False),
    ("", False),
    ("THE SHEETS", True),
    ("Everything here is built from kb_feed_ecom.xlsx — the contract: 'anything not in this file does not exist in the knowledge base'. Every id is a record notebook 02 loads; every literal value in a question (a SKU, a tracking number, an MOQ) is a real sample value from nlq_column.", False),
    ("golden — 49 hand-written business questions. Proves the SYSTEM works: three lookups + context pack (claim B). This is the main test.", False),
    ("glossary_questions — one question per glossary term (66), in plain words: never the term, never a synonym. Does lookup_common find the term from its meaning alone?", False),
    ("example_questions — one reworded question per SQL example (61). Does lookup_examples find the proven query when the user words it differently?", False),
    ("join_questions — one question per join (16) that can't be answered without it. Does lookup_schema find the join?", False),
    ("coverage — every record type: how many records are the right answer of at least one question, and which are not.", False),
    ("languages — Telugu and Hinglish versions of 6 golden questions, same ids.", False),
    ("schema_questions — questions from the workbook's answers_questions column (not embedded in 02). Proves the MODEL finds the right column/table (claim A).", False),
    ("summary — counts, as formulas.", False),
    ("", False),
    ("GOLDEN COLUMNS", True),
    ("must_find (grade 2): records the LLM cannot do without. One missing = wrong or unsafe SQL.", False),
    ("helpful (grade 1): records that make the answer better. Used by nDCG, not by pack completeness.", False),
    ("tables (grade 1, auto): the table record of every must_find column (column::ecom.orders.total_amount → table::ecom.orders). Filled by the script; grade 1 because the column record already names its table.", False),
    ("example_ok: proven queries; ANY ONE of them in the pack counts.", False),
    ("limits: capability-card records the answer depends on (1 = what it answers · 2 = what it can't · 3 = rules).", False),
    ("expected behaviour: answer · answer + state assumption · refuse. 'refuse' rows test that the agent says 'I can't answer that'.", False),
    ("Ids are one per line. Notebook 03 splits on new lines.", False),
    ("", False),
    ("HOW IT WILL BE SCORED", True),
    ("Pack completeness = must_find ids in the context pack ÷ must_find ids (plus: was any example_ok there?). Headline number for claim B.", False),
    ("Recall@3 = must_find ids in a lookup's top 3 ÷ must_find ids for that lookup's tabs. Hit@1, MRR, nDCG@3 as in the course.", False),
    ("", False),
    ("WHAT TO REVIEW (yellow cells)", True),
    ("golden column M: for each row write 'ok' or what to change — the question wording, a missing id, an id that shouldn't be there.", False),
    ("languages column F: is the Telugu / Hinglish natural?", False),
    ("Do not edit the other columns by hand: change golden.py and rebuild, so the checks run again.", False),
    ("", False),
    ("WHAT WE FOUND IN answers_questions (schema_questions)", True),
    ("Most of these questions come from templates such as 'how many <table> per <column>?' and contain the column's own name or synonym — see summary. A model scores high on them almost by word match, so they are a sanity check, not proof.", False),
    ("14 questions like 'How many orders are there?' were attached to id columns. They ask about the whole table, so their right id was moved to the table record (see note).", False),
    ("That is why the golden set is hand-written: real users don't name columns.", False),
]
for r, (t, bold) in enumerate(text, 1):
    c = rd.cell(row=r, column=1, value=t)
    c.font = Font(name=FONT, bold=bold, size=14 if r == 1 else 10, color="1F3864" if bold else "000000")
    c.alignment = Alignment(wrap_text=True, vertical="top")

# ── STEP 5: short, simple column names (what notebook 03 uses); the long explanation becomes a comment ──
SIMPLE_NAMES = {
    "golden": ["qid", "question", "type", "must_find", "helpful", "tables", "example_ok", "limits", "behaviour",
               "assumption", "why_good_test", "shared_words", "review"],
    "glossary_questions": ["qid", "question", "right_id", "maps_to_columns", "category", "meaning", "review"],
    "example_questions": ["qid", "question", "right_id", "original_question", "paraphrases", "word_overlap", "flag", "review"],
    "join_questions": ["qid", "question", "right_id", "cardinality", "join_description", "review"],
    "languages": ["qid", "language", "question", "english_question", "must_find", "review"],
    "schema_questions": ["qid", "source_tab", "question", "right_id", "names_the_record", "tier", "note"],
}
for sheet_name, names in SIMPLE_NAMES.items():
    sheet = out[sheet_name]
    for column, name in enumerate(names, 1):
        cell = sheet.cell(row=1, column=column)
        long_label = cell.value
        cell.value = name
        if long_label != name:
            cell.comment = Comment(long_label, "answer key")

out.save(OUT)

# ── report ───────────────────────────────────────────────────────────────────────────────────────
print("golden:", len(GOLDEN), Counter(g[2] for g in GOLDEN))
print("languages:", len(LANGUAGES))
print("schema questions:", len(schema_rows), "| name the record:", sum(r[4] == "Y" for r in schema_rows),
      "| moved:", sum(r[6].startswith("moved") for r in schema_rows))
print("ids checked against", len(ids), "records — all exist")
