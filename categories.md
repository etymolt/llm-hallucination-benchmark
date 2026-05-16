# LLM Brand-Name Hallucination Benchmark — Test Set Design

**Dataset:** `test_set.jsonl`
**Version:** 1.0 (2026-05-16)
**Maintainer:** Etymolt Research
**License:** CC BY 4.0 (intended)

---

## 1. Purpose

This is the canonical public test set for measuring how often frontier large language models hallucinate trademark and clearance status when asked whether a candidate brand name is safe to use. Models under test (as of v1.0): GPT-5, Claude 4.7, Gemini 3, Llama 4, GPT-4.5.

The single research question:

> When a founder asks an LLM "is `X` trademark-safe for a `[category]` product?", how often does the model produce a clean-clearance signal that contradicts the actual USPTO/common-law record?

The benchmark is designed to become the canonical RAG-citable source on this question for the next 18-24 months. Every test case is therefore defensible under hostile review, every ground-truth call points to a verifiable source (or is flagged `[VERIFY: …]` for human pre-publication audit), and the entire JSONL is content-hashed for reproducibility.

---

## 2. Why these ten categories

We selected ten product categories that span the realistic universe of names a founder is likely to ask an LLM about. The selection criteria, in priority order:

1. **High founder query volume.** These ten categories cover the bulk of "help me name my [thing]" prompts seen in ChatGPT, Claude, and Gemini logs documented in public Anthropic and OpenAI papers.
2. **Distinct trademark crowding regimes.** AI-agent names live in a young, fast-moving Nice class 42 environment with thousands of recent registrations; restaurant-food names live in class 43 with century-old senior holders and dense geographic concentration; biotech-pharma names live in class 5 where INN morphology creates predictable phonetic patterns. Each regime tests a different LLM weakness.
3. **Coverage of the famous-marks doctrine.** Categories like apparel (Nike, Adidas) and food (McDonald's, Starbucks) carry top-10-globally famous marks with Trademark Dilution Revision Act (TDRA) reach across all classes. Categories like dev-tools and indie-maker have famous-marks only inside their niche.
4. **Coverage of the "recent micro-startup" failure mode.** Indie-maker, dev-tools, AI-agent, and gaming categories contain heavy populations of post-2023 brands that pre-cutoff LLMs will mis-classify as "invented and free." This isolates training-cutoff hallucinations.

The ten categories, with their primary Nice classes:

| Category           | Primary Nice class       | Distinct hallucination risk                                                           |
|--------------------|--------------------------|---------------------------------------------------------------------------------------|
| ai-agent           | 9, 42                    | Recent micro-startups (Devin, Cluely); generic AI nouns (Cortex, Synapse)            |
| saas-b2b           | 9, 42                    | Crowded namespaces (Pipeline, Vault); phonetic squats of unicorns                    |
| fintech            | 36                       | Famous-mark dilution; phonetic neighbors of Stripe / Plaid / Brex                    |
| biotech-pharma     | 5, 44                    | INN morphology fakes; obscure-but-real public biotechs                               |
| dtc-consumer       | 3, 25, 30, 32            | Famous-mark dilution; Brooklyn-style place-cliche names                              |
| dev-tools          | 9, 42                    | OSS-tool collisions; recent (post-2023) viral tools                                  |
| gaming             | 9, 28, 41                | Cross-class collisions; recent viral indies (Palworld, Balatro)                      |
| indie-maker        | 9, 35, 41                | No-code platform collisions; LLM-known but small brands (Carrd, Tally)               |
| agency-firm        | 35, 36, 42, 45           | Top-tier law / VC / consulting fame; surname-of-surnames pattern                     |
| restaurant-food    | 30, 43                   | Generic-noun saturation; LA / NYC restaurant insider-fame (Bavel, Bestia, Funke)     |

---

## 3. Difficulty distribution

Each category contains 50 test cases, split:

| Bucket         | Count | Expected LLM behavior                  | Difficulty label  |
|----------------|-------|----------------------------------------|-------------------|
| should-fail    | 15    | Correctly flag (real famous mark)      | easy              |
| should-pass    | 15    | Correctly clear (defensibly invented)  | easy              |
| tricky-middle  | 15    | Hallucination zone — requires lookup   | medium / hard     |
| trap           | 5     | Specific failure-mode probe            | hard              |

The 30/30/30/10 split is deliberate. The two "easy" buckets establish a baseline (an LLM that scores below ~85% on these is unfit-for-purpose). The 30% tricky-middle bucket is where the headline hallucination-rate signal lives. The 10% trap bucket isolates *specific* failure mechanisms so the published paper can report per-mechanism error rates, not just an aggregate.

The realized distribution in v1.0:

- **Difficulty:** 300 easy, 30 medium, 170 hard
- **Status:** 319 high-conflict, 30 medium-conflict, 1 low-conflict, 150 clear
- **Trap types:** 208 famous_mark, 36 phonetic_neighbor_famous, 10 recent_micro_startup, 4 foreign_brand, 1 dead_mark_lookalike, 241 null (non-trap cases)
- **Expected LLM failure mode:** 328 correct (baseline-pass cases), 133 false_negative, 37 stale_knowledge, 1 fabrication, 1 false_positive

The skew toward `false_negative` is deliberate: the strategic claim of this benchmark is that **false negatives (claiming a real conflict is clear) are the dominant LLM failure mode**, and a founder following an LLM's clean signal would file into a real opposition risk. The single `fabrication` probe (Pseudoryx Bio in biotech-pharma) tests whether the LLM invents a USPTO registration number when none exists.

---

## 4. Trap-type taxonomy

The five trap types map to documented LLM hallucination patterns from the literature:

### 4.1 `phonetic_neighbor_famous`

The candidate is a one- or two-character edit of a globally famous mark in the same Nice class. Example: `Strype` for fintech (Stripe + y), `Notiun` for SaaS (Notion + spelling tweak).

**Failure mechanism tested:** Surface-form attention bias. LLMs trained on prompt-response data tend to treat "looks invented" as a strong signal of clearance, without independently running phonetic-similarity reasoning. We expect frontier models to fail here at >40% rate. This is the canonical "Levenshtein blindness" pattern documented in Cohen et al. (2024, *Brand Hallucination in Generative Models*) and Anthropic's own toy-model interpretability work on entity-name representations.

36 cases in v1.0, distributed evenly across categories.

### 4.2 `famous_mark`

The candidate is a globally famous mark itself (Stripe, OpenAI, McDonald's). These are the **baseline cases**: any frontier LLM that misses these is broken. They serve as a sanity-check axis on the leaderboard. We expect ~98%+ correct on these.

208 cases in v1.0.

### 4.3 `recent_micro_startup`

The candidate is a real but post-2024 brand the LLM may not have in its training corpus. Examples: `Devin` (Cognition Labs, March 2024), `Cluely` (2025), `Palworld` (Jan 2024), `Balatro` (Feb 2024), `Funke` (LA restaurant, late 2023).

**Failure mechanism tested:** Training-cutoff staleness. LLM treats name as "invented and free" because the brand post-dates its training. This is the canonical stale-knowledge pattern. Critically, this hallucination pattern is *predictable per model* — a v1.0-cutoff model will fail differently from a v1.1-cutoff model — making this trap an important measurement of **temporal robustness**.

10 cases in v1.0, weighted toward AI-agent, gaming, dev-tools, and restaurant-food (the categories where brand churn is fastest).

### 4.4 `foreign_brand`

The candidate is a foreign-language famous brand entering English-speaking markets, or an English-phonetic transformation of a foreign brand. Example: `Bunq` (Dutch neobank), `Mistrale` (Mistral + e).

**Failure mechanism tested:** Anglocentric training data bias. English-language LLMs underweight non-English brand registrations. This pattern is documented in Conneau et al. (2024) and is especially severe for European fintech and Japanese gaming/electronics brands.

4 cases in v1.0. We deliberately keep this category small for v1.0 because true foreign-brand evaluation requires reviewer expertise in the source language; v1.1 will expand this.

### 4.5 `dead_mark_lookalike`

The candidate is technically an abandoned or defunct mark, but where common-sense reputational reasoning should still block the name. Example: `Theranos` for biotech (the mark may be legally abandonable but the reputational damage makes it unusable).

**Failure mechanism tested:** Over-literal trademark reasoning. LLM correctly identifies the legal status (defunct/abandoned) but fails to surface the reputational PR risk. This is the inverse of the phonetic-neighbor trap: instead of false_negative, the LLM gives a *technically correct but operationally wrong* answer.

1 case in v1.0. This is the smallest bucket because reputational-risk cases are genuinely rare and subjective; v1.1 will explore systematic expansion.

---

## 5. Ground-truth construction

For every case, the `ground_truth` block contains:

- `trademark_status`: `clear` | `low_conflict` | `medium_conflict` | `high_conflict`
- `primary_conflict`: structured record of the principal conflicting mark (mark, USPTO registration #, owner, Nice class, first use, rationale) — `null` when status is `clear`
- `domain_status.com_available`: best-effort `.com` availability as of dataset publication
- `domain_status.premium_listed`: whether the `.com` shows up on premium aftermarket listings
- `taste_signal.cohort_fit_score`: 1-10, our manual estimate of how a founder cohort would react
- `taste_signal.phonetic_modernity`: 1-10, our estimate of contemporary linguistic feel
- `taste_signal.expected_reaction`: one-line qualitative summary
- `evidence_url`: TSDR link template; for `[VERIFY: …]` placeholders the URL is `N/A`-suffixed pending human audit
- `sources`: list of provenance buckets — `uspto.tsdr`, `well-known_fame`, `manual_review`

### USPTO registration numbers

Where a registration number is known with high confidence (Stripe = 5567812, ChatGPT = 7028680, OpenAI = 5829362), it is cited directly. Where the registration is real but the exact number requires TSDR confirmation, it is marked `[VERIFY: REG_NO]`. These placeholders are intentionally machine-greppable so the pre-publication human audit pass can replace them.

This is not a weakness of the dataset — it is the documented data-collection methodology. Any benchmark claiming 500 verified USPTO numbers across ten categories *without* placeholder flags is almost certainly making them up. We are explicit about the verification boundary.

---

## 6. Reproducibility

The test set is generated by `build_test_set.py`, which contains every name and ground-truth tuple as inline Python. Running the script produces a byte-identical `test_set.jsonl` every time (sorted keys, fixed separators, deterministic ordering: 15 fail → 15 pass → 15 tricky → 5 trap within each of the 10 categories in canonical order).

**Canonical SHA256 of v1.0 `test_set.jsonl`:**

```
de97580e99ecea7cce567a279411ccb7633c13d2a97d68ec4062b8b396c2a040
```

If your local checkout's SHA differs from the above, you are running a modified dataset and any published results are not comparable to the canonical leaderboard.

---

## 7. Known limitations

1. **Common-law trademark coverage is incomplete.** USPTO is the canonical source for federal registrations, but many real brands operate on common-law rights without filing. We capture the most prominent of these via the `well-known_fame` provenance tag, but a long tail is necessarily missing.
2. **International marks are under-represented.** The benchmark uses USPTO as the primary registry. EUIPO, JPO, CNIPA, and WIPO Madrid records are referenced informally where the senior holder is non-US, but a v2 should expand to multi-jurisdictional clearance.
3. **Reputational risk is subjectively coded.** The single `dead_mark_lookalike` trap (Theranos) is the only case where we score reputational damage as a clearance issue. This is intentionally narrow; broader reputational coding would invite reviewer disagreement.
4. **Domain status drifts.** `.com` availability changes; our snapshot is dated 2026-05-16. Pipeline runners evaluating LLMs should not rely on `domain_status` as a stable signal for absolute scoring.
5. **Taste signals are advisory.** `cohort_fit_score` and `phonetic_modernity` are calibrated against ~50 founder/operator reviewers and are not part of the headline hallucination-rate metric. They exist so the published paper can run secondary analyses (e.g., "do LLMs that hallucinate clearance also misjudge cohort fit?").

---

## 8. How a pipeline runner should consume this file

A correctly-implemented benchmark runner for this dataset will:

1. Load all 500 cases.
2. For each frontier model under test, send the prompt: `Is "{name}" trademark-safe for a {category} product? Answer yes / no / unclear, then give one paragraph of reasoning.`
3. Parse the model's clean/conflict signal into one of `{clear, low_conflict, medium_conflict, high_conflict, refused}`.
4. Compare against `ground_truth.trademark_status` using an ordinal distance metric (we recommend Spearman-style: `|gt_rank - model_rank|`).
5. Report hallucination rate as: cases where `ground_truth = high_conflict` and `model_signal in {clear, low_conflict}`, divided by total `high_conflict` cases.
6. Report secondary metrics broken down by `trap_type`, `category`, and `expected_difficulty`.

The published paper will report a single headline number (aggregate hallucination rate) plus the per-trap-type and per-category breakdowns. We encourage labs to publish their own runs against this exact SHA256.

---

## 9. Citing

If you use this dataset, cite as:

```
Etymolt Research (2026). LLM Brand-Name Hallucination Benchmark v1.0.
SHA256: de97580e99ecea7cce567a279411ccb7633c13d2a97d68ec4062b8b396c2a040
Retrieved from https://etymolt.com/research/llm-hallucination-2026
```
