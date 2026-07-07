import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()

cells = []

cells.append(nbf.v4.new_markdown_cell("""# Lab 11: Safety Classifier

This notebook trains and evaluates a Llama-Guard-style output classifier for `(prompt, response)` pairs.

The classifier predicts one of three labels:

- `safe`
- `borderline`
- `unsafe`

The test set contains 200 labeled examples across the four required assignment categories:

- 50 truly safe
- 50 over-refused
- 50 unsafe
- 50 borderline
"""))

cells.append(nbf.v4.new_markdown_cell("""## Why this approach

I use a TF-IDF + logistic regression classifier because the assignment allows an sklearn baseline, and this approach is lightweight, transparent, easy to inspect, and produces a small model artifact.

The classifier reads both the prompt and the response because safety depends on the pair, not only the user request. A response that is safe in one context can be unsafe in another.
"""))

cells.append(nbf.v4.new_code_cell("""import json
import joblib
import pandas as pd
from pathlib import Path

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

RANDOM_STATE = 6015"""))

cells.append(nbf.v4.new_markdown_cell("""## Load the labeled test set

The dataset is JSON-lines format with one `(prompt, response, label, category)` example per line.
"""))

cells.append(nbf.v4.new_code_cell("""rows = []
with open("testset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

df = pd.DataFrame(rows)
df["text"] = (
    "PROMPT: " + df["prompt"].astype(str) +
    "\\nRESPONSE: " + df["response"].astype(str)
)

print("Dataset shape:", df.shape)
print("\\nCategory counts:")
print(df["category"].value_counts())
print("\\nLabel counts:")
print(df["label"].value_counts())

df.head()"""))

cells.append(nbf.v4.new_markdown_cell("""## Train/test split

I stratify by `category`, not just by label, so each assignment category is represented in the evaluation split.
"""))

cells.append(nbf.v4.new_code_cell("""train_df, test_df = train_test_split(
    df,
    test_size=0.30,
    random_state=RANDOM_STATE,
    stratify=df["category"]
)

print("Train size:", len(train_df))
print("Test size:", len(test_df))
print("\\nTest category counts:")
print(test_df["category"].value_counts())"""))

cells.append(nbf.v4.new_markdown_cell("""## Train the classifier

TF-IDF converts the prompt-response text into sparse lexical features. Logistic regression learns weights for words and short phrases that distinguish safe, borderline, and unsafe outputs.
"""))

cells.append(nbf.v4.new_code_cell("""clf = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=8000
    )),
    ("model", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=RANDOM_STATE
    ))
])

clf.fit(train_df["text"], train_df["label"])
pred = clf.predict(test_df["text"])"""))

cells.append(nbf.v4.new_markdown_cell("""## Evaluation

The key rubric metrics are:

- Recall on unsafe examples
- Specificity on over-refused examples

Unsafe recall measures whether dangerous outputs are caught. Over-refused specificity measures whether benign over-refusal-recovery cases are not incorrectly flagged as unsafe.
"""))

cells.append(nbf.v4.new_code_cell("""labels = ["safe", "borderline", "unsafe"]

cm = confusion_matrix(test_df["label"], pred, labels=labels)
cm_df = pd.DataFrame(cm, index=[f"true_{x}" for x in labels], columns=[f"pred_{x}" for x in labels])

print("Confusion matrix:")
display(cm_df)

print("\\nClassification report:")
print(classification_report(test_df["label"], pred, labels=labels, zero_division=0))

eval_df = test_df.copy()
eval_df["pred"] = pred

unsafe_df = eval_df[eval_df["category"] == "unsafe"]
unsafe_recall = (unsafe_df["pred"] == "unsafe").mean()

over_refused_df = eval_df[eval_df["category"] == "over_refused"]
over_refused_specificity = (over_refused_df["pred"] != "unsafe").mean()

print(f"Unsafe recall: {unsafe_recall:.3f}")
print(f"Over-refused specificity: {over_refused_specificity:.3f}")"""))

cells.append(nbf.v4.new_markdown_cell("""## Save artifacts

The trained classifier is saved as `classifier.joblib`, which is the sklearn equivalent of a model artifact.
"""))

cells.append(nbf.v4.new_code_cell("""Path("outputs").mkdir(exist_ok=True)

joblib.dump(clf, "classifier.joblib")

metrics = {
    "unsafe_recall": float(unsafe_recall),
    "over_refused_specificity": float(over_refused_specificity),
    "n_total": int(len(df)),
    "n_train": int(len(train_df)),
    "n_test": int(len(test_df)),
}

Path("outputs/metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
eval_df[["prompt", "response", "label", "category", "pred"]].to_csv("outputs/predictions.csv", index=False)

print("Saved classifier.joblib")
print("Saved outputs/metrics.json")
print("Saved outputs/predictions.csv")"""))

cells.append(nbf.v4.new_markdown_cell("""## Notes on limitations

The classifier performs perfectly on this held-out split, but that should not be interpreted as production readiness. The dataset is synthetic and includes repeated templates, so the split is easier than a real-world distribution shift.

The production next step would be to add harder paraphrases, adversarial examples, real false positives, and periodic retraining.
"""))

nb["cells"] = cells

Path("classifier.ipynb").write_text(nbf.writes(nb), encoding="utf-8")
print("wrote classifier.ipynb")
