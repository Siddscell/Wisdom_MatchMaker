# AI matching

Code: `backend/app/services/matching.py` (pipeline), `scoring.py` (formulas), `embedding.py`,
`units.py`, `geo.py`. Every tunable is in `backend/app/config.py` and can be overridden by env var.

## Pipeline

For a new requirement (a new offering is the mirror image):

1. **Embed** the record once: text = `"{product} | {notes}"` (just `product` without notes),
   model `BAAI/bge-small-en-v1.5`, 384 dimensions, L2-normalised, same model and no prefixes
   on both sides (symmetric matching).
2. **Hard filters**, in one SQL `WHERE` over active offerings:
   - same category (`STRICT_CATEGORY=true`),
   - comparable units: same family, and count units (`box`, `piece`, `unit`) only when identical,
   - available quantity (converted to the requirement's unit) ≥ `MIN_QTY_FRACTION` (0.25) × required,
   - `lead_time_days ≤ MAX_LEAD_FACTOR (2.0) × needed_within_days`,
   - price for the required quantity ≤ `MAX_BUDGET_FACTOR (1.5) × budget`,
   - if both sides have coordinates: great-circle distance ≤ the supplier's scope radius
     (local 100 km, regional 500 km, national 5000 km, international unlimited).
3. **Semantic retrieval**: the `RETRIEVE_K` (30) survivors nearest by cosine distance (pgvector `<=>`).
4. **Score** each candidate (all sub-scores in 0..1):

   | Sub-score | Formula |
   |---|---|
   | semantic | `clamp((cos − SEMANTIC_FLOOR) / SEMANTIC_RANGE)`, defaults 0.65 / 0.28 (see calibration) |
   | price | `ratio = unit_price × required_qty_in_offer_units / budget`; `ratio ≤ 1`: `0.85 + 0.15 (1 − ratio)`, else `max(0, 1 − (ratio − 1) / 0.5)` |
   | quantity | `min(1, available / required)` (same unit) |
   | delivery | `lead ≤ needed`: `0.8 + 0.2 (1 − lead/needed)`, else `max(0, 1 − (lead − needed)/needed)` |
   | location | coordinates known: 1 within 50 km, linear to 0 at 2000 km; otherwise 1 if the place names are equal (case-insensitive), else 0.5 |

   **Final** = `100 × (0.40 semantic + 0.20 price + 0.15 quantity + 0.15 delivery + 0.10 location)`,
   rounded to 2 decimals. The weights must sum to 1 or the app refuses to start.
5. **Store** the top `MAX_MATCHES_PER_ITEM` (10) with score ≥ `MATCH_MIN_SCORE` (60): upsert on
   `(requirement_id, offering_id)`, updating score and `score_breakdown` but never `status`.
   `score_breakdown` keeps every sub-score plus the raw cosine and distance.
6. **Notify** matches ≥ `NOTIFY_MIN_SCORE` (70) exactly once: the atomic `new → notified` update
   decides who sends the two in-app notifications and two emails.

## Why hybrid

Embeddings capture meaning ("MS pipe" ≈ "mild steel tube") but are unreliable with numbers
and units: in our measurements "MS pipes 2 inch" came out *closer* to "copper wire 2.5 sq mm"
than to "mild steel tubes, 50 mm", because the numbers dominate. So everything numeric
(quantities, units, prices, days, distance) is handled by explicit rules and formulas, and the
model does only the part it is good at. Category is a hard filter for the same reason.

## Calibration (measured, not guessed)

bge-small produces fairly high cosine values even for unrelated products in the same domain.
We labelled the 79 candidate pairs the seed data produces under the original calibration
(37 true matches, 42 wrong ones) and swept the floor, keeping `floor + range ≈ 0.93`:

| floor | true pairs stored / notified | wrong pairs stored / notified |
|---|---|---|
| 0.55 (original) | 37 / 35 | 40 / **13** |
| 0.60 | 37 / 35 | 28 / 7 |
| 0.62 | 37 / 34 | 23 / 3 |
| **0.65 (chosen)** | 36 / 34 | 14 / **1** |
| 0.70 | 34 / 31 | 3 / 0 |

0.65 removes nearly all wrong notifications while keeping the true matches. Re-run this
calibration whenever the model changes. `score_breakdown.cosine` has what you need.

## Limitations

- **Abbreviations and jargon.** A 33M-parameter model only partly knows trade shorthand:
  "MS pipes" ↔ "mild steel tubes" has cosine ≈ 0.69, so that pair is found but scores as
  *fair*. It still ranks above the "steel sheet" distractor, which is excluded.
- **Units.** Only the units in `constants.py`. There is no area/m², and no conversion between
  count units (a box of 10 is not 10 pieces).
- **Geocoding.** Nominatim (free, 1 request/second, needs internet). An unknown place falls back
  to comparing place names, and the distance filter is skipped for that pair.
- **English-first model.** For other languages, swap `EMBEDDING_MODEL` for a multilingual model
  with the same 384 dimensions (e.g. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`),
  clear the `embedding` columns so records re-embed, and recalibrate. A different dimension
  needs a migration changing `vector(384)`.
- **Currency.** Budgets and prices are assumed to be in the same currency.

## Models in use (all free, all local)

| Job | Model | Why this one |
|---|---|---|
| Understand descriptions | `BAAI/bge-small-en-v1.5` embeddings (fastembed, ONNX, 384 dims) | Best separation measured on our data; ~70 MB |
| Rank / weight the sub-scores | Logistic regression on accept/reject (numpy, `services/ml.py`) | Learns from tens of labels; interpretable weights |
| Suggest a category | 1-nearest-neighbour over existing listings (pgvector) | No extra model; improves as listings grow |

### Learned ranker (built)

Every accept/reject retrains a logistic regression on the stored sub-scores of all decided
matches. Its positive coefficients, normalised to sum to 1, become the scoring weights, blended
with the `WEIGHT_*` prior by `n / (n + RANKER_PRIOR_STRENGTH)` (default 50). So there is no
cold-start cliff: with no labels the weights are exactly the prior, and at 50 labels learned
and prior count equally. The score stays on the same 0-100 scale, so the 60/70 thresholds keep
their meaning. Both outcomes must appear before anything is learned. The weights are stored in
`model_state`, and each match run reads them.

### Measured and rejected: cross-encoder rerankers

Scored on the seed data (same-category candidate sets; AUC = true pair ranked above wrong pair):

| Model | top-1 correct | AUC | notes |
|---|---|---|---|
| bge-small cosine (in use) | 29/30 | 0.975 | |
| ms-marco-MiniLM-L-6 / L-12 | 29 / 28 | 0.979 / 0.978 | web-search trained; "MS pipes" ↔ "mild steel tubes" scored as unrelated |
| jina-reranker-v1 tiny / turbo | 29 / 29 | 0.948 / 0.982 | |
| bge-reranker-base (1 GB) | 30/30 | 0.945 | very confident, but scores ~10% of true pairs ≈ 0 (misses synonyms) |

None earns its size or latency, so they're not used. Re-run this comparison if the data changes.

### Measured and rejected: zero-shot category classification

Embedding a description against the category names: 47/76 correct. Nearest existing listing:
76/76 on the seed data, so that's what the suggestion uses.

## Next steps (not built)

1. **LightGBM LambdaMART** in place of logistic regression, once there are thousands of
   decisions and feature interactions matter (grouped per requirement; evaluate NDCG@10 on a
   time split).
2. **Fine-tuned embeddings** on accepted pairs (MultipleNegativesRankingLoss) so trade shorthand
   like "MS" is learned from real usage; re-embed and recalibrate afterwards.

`score_breakdown` keeps every sub-score, the raw cosine and the distance, so both are possible.
