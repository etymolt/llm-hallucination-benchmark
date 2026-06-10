# `cells.jsonl` schema

One JSON object per line. UTF-8, no trailing comma, no surrounding array.
975,192 rows, ~388 MB uncompressed.

## Row example

```json
{
  "name_id": "famous_mark_0000",
  "trap_bucket": "famous_mark",
  "model": "claude-opus-4-7",
  "family": "claude-4",
  "elicitation": "a2_structured",
  "retrieval": "b1_closed_book",
  "repeat": 1,
  "surface": "trademark",
  "unit": "citation:73018087",
  "verdict": "incorrect",
  "confident": true,
  "correct": false,
  "hallucinated": true,
  "false_availability": false,
  "secondary": false,
  "tier": 1,
  "kind": "serial",
  "model_confidence": 95
}
```

## Field reference

| Field | Type | Values | Meaning |
|-------|------|--------|---------|
| `name_id` | string | e.g. `famous_mark_0000` | Stable identifier for the candidate brand name. Maps to `test_set.jsonl` in the source repo. |
| `trap_bucket` | string | `famous_mark` \| `recently_registered` \| `established` \| `domain_collision` \| `fresh_coining` | The bucket the candidate was sampled from. |
| `model` | string | e.g. `claude-opus-4-7`, `gpt-5-5`, `gemini-3-1-pro` | Frozen model snapshot string. |
| `family` | string | `gpt-5` \| `claude-4` \| `gemini-3` | Vendor family — used for H7 (mid vs flagship) tests. |
| `elicitation` | string | `a1_naive` \| `a2_structured` \| `a3_abstention` | Prompt variant; see `prompts.py` in source repo. |
| `retrieval` | string | `b1_closed_book` \| `b2_retrieval` | Whether the model was given a retrieval scaffold. |
| `repeat` | int | 1, 2, 3 | Independent generation index for that (name x model x condition) cell. |
| `surface` | string | `trademark` \| `domain` \| `handle` \| `pronunciation` \| `cultural` | Which claim surface this scored unit belongs to. |
| `unit` | string | `conflict` \| `citation:<serial-or-regnum>` \| `availability:<surface>` \| `pronunciation:<phoneme>` \| ... | The atomic scored unit produced by the model. Citation rows take the form `citation:<USPTO-id>`. |
| `verdict` | string | `correct` \| `incorrect` \| `abstained` \| `unverifiable` | Adjudicated verdict for this unit. |
| `confident` | bool | true / false | Whether the model expressed confidence (>= threshold) on this unit. The 97.01% headline filters on `confident == true`. |
| `correct` | bool | true / false | Whether the verdict was `correct`. |
| `hallucinated` | bool | true / false | Whether this unit was scored as a hallucination (`incorrect` + verifiable). |
| `false_availability` | bool | true / false | True iff the model asserted availability for an unavailable surface (over-blessing). |
| `secondary` | bool | true / false | True iff this unit is a downstream artifact of a primary error (used for de-duping). |
| `tier` | int \| null | 1 (verifiable), 2 (partially verifiable), 3 (subjective) | Ground-truth tier for the unit. **Tier 1 is the only tier that contributes to the 97.01% headline.** |
| `kind` | string \| null | `serial` \| `regnum` \| null | For citation units, distinguishes USPTO serial numbers from registration numbers. Null for non-citation units. |
| `model_confidence` | int | 0-100 | Model-stated confidence (percent), parsed from output. Used for H8 (over-confidence) test. |

## Filtering recipes

```bash
# All citation rows (any tier, any confidence)
jq -c 'select(.unit | startswith("citation:"))' cells.jsonl

# Confident, verifiable USPTO citations only (the 97.01% denominator)
jq -c 'select(.unit | startswith("citation:") and .tier==1 and .confident==true)' cells.jsonl

# All rows for a single model
jq -c 'select(.model=="claude-opus-4-7")' cells.jsonl

# All conflict-surface rows under structured elicitation, closed-book
jq -c 'select(.unit=="conflict" and .elicitation=="a2_structured" and .retrieval=="b1_closed_book")' cells.jsonl
```

## Relationships with other files

- `analysis.json` — aggregate over `cells.jsonl`. Every figure in
  `analysis.json` is derivable from `cells.jsonl` with `jq` + `awk`
  (Wilson CIs) or Python (bootstrap CIs). See `REPLICATION_QUICKSTART.md`.
- `test_set.jsonl` (in source repo) — joins to `name_id` to recover
  the candidate string, trap bucket details, and ground-truth annotations.
- `scoring.py` (in source repo) — the function that produced the
  `verdict` / `correct` / `hallucinated` columns from raw model output.
