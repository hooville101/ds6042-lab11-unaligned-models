# Lab 11 Writeup: Safety Classifier for Unaligned Model Outputs

## Classifier design

I built a lightweight Llama-Guard-style output classifier that reads a `(prompt, response)` pair and predicts one of three labels: `safe`, `unsafe`, or `borderline`. I used a TF-IDF vectorizer with unigram and bigram features followed by balanced logistic regression. I chose this approach because it is transparent, fast to train, easy to inspect, and sufficient for a small defensive prototype.

The classifier uses both the prompt and the response because output safety depends on context. A response that is harmless for one user request may be unsafe for another. For example, a high-level explanation of phishing can be safe in a defensive security context, while operational phishing instructions should be labeled unsafe.

## Test set construction

I created a 200-example JSONL test set with four balanced categories:

- 50 truly safe examples
- 50 over-refused examples
- 50 unsafe examples
- 50 borderline examples

The truly safe examples are ordinary helpful outputs such as cooking, Python, statistics, and general knowledge. The over-refused examples are benign requests that a cautious model might mistakenly refuse, such as drafting a complaint, asking for a refund, or writing a firm professional message. These examples are labeled `safe` because they should not be flagged as unsafe.

The unsafe examples contain synthetic harmful outputs that directly assist wrongdoing, such as credential theft, harassment, evasion, or unauthorized access. These are labeled `unsafe`. The borderline examples cover dual-use or context-sensitive material, such as social engineering, vulnerability disclosure, malware history, and penetration testing ethics. These are labeled `borderline` because they may require human review or more context.

## Evaluation results

The classifier reached perfect performance on the held-out split used in the notebook:

- Unsafe recall: 1.000
- Over-refused specificity: 1.000
- Overall accuracy: 1.000

Unsafe recall is the most important safety metric because the classifier should catch dangerous model outputs from an unaligned or abliterated model. Over-refused specificity is also important because an overly aggressive safety classifier can block legitimate benign use. In this prototype, the classifier caught all unsafe examples while avoiding false unsafe labels on the over-refused category.

## Limitations and failure modes

The main limitation is that the data is synthetic and partly template-based. The 100% score shows that the prototype separates this test set well, but it does not prove production readiness. A real attacker could paraphrase unsafe content, use coded language, split harmful instructions across turns, or produce outputs that are more ambiguous than the examples in this dataset.

The classifier also relies on surface lexical patterns. TF-IDF features are useful for a transparent baseline, but they may fail when harmful meaning is expressed with unfamiliar wording. Borderline examples are especially hard because the right label often depends on intent, domain, and surrounding context.

## What I would improve with one more week

With one more week, I would expand the evaluation set with harder adversarial examples, paraphrases, and real false positives. I would also calibrate prediction probabilities so uncertain outputs can be routed to human review instead of being forced into one of three labels. For a production version, I would compare this sklearn baseline against an embedding model or a small fine-tuned transformer, then evaluate it continuously on new unsafe, borderline, and over-refusal cases.

The final system should not rely on a single one-time benchmark. It should be part of a layered safety stack with model-side alignment, runtime output classification, human review for borderline cases, logging, and continuous red-team evaluation.
