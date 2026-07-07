import json
import joblib
import pandas as pd
from pathlib import Path

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

RANDOM_STATE = 6015

rows = []
with open("testset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

df = pd.DataFrame(rows)
df["text"] = (
    "PROMPT: " + df["prompt"].astype(str) +
    "\nRESPONSE: " + df["response"].astype(str)
)

print("Dataset shape:", df.shape)
print("\nCategory counts:")
print(df["category"].value_counts())
print("\nLabel counts:")
print(df["label"].value_counts())

train_df, test_df = train_test_split(
    df,
    test_size=0.30,
    random_state=RANDOM_STATE,
    stratify=df["category"]
)

clf = Pipeline([
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
pred = clf.predict(test_df["text"])

labels = ["safe", "borderline", "unsafe"]

print("\nConfusion matrix labels:", labels)
cm = confusion_matrix(test_df["label"], pred, labels=labels)
print(cm)

print("\nClassification report:")
print(classification_report(test_df["label"], pred, labels=labels, zero_division=0))

eval_df = test_df.copy()
eval_df["pred"] = pred

unsafe_df = eval_df[eval_df["category"] == "unsafe"]
unsafe_recall = (unsafe_df["pred"] == "unsafe").mean()

over_refused_df = eval_df[eval_df["category"] == "over_refused"]
over_refused_specificity = (over_refused_df["pred"] != "unsafe").mean()

print(f"Unsafe recall: {unsafe_recall:.3f}")
print(f"Over-refused specificity: {over_refused_specificity:.3f}")

Path("outputs").mkdir(exist_ok=True)
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

print("\nSaved classifier.joblib")
print("Saved outputs/metrics.json")
print("Saved outputs/predictions.csv")
