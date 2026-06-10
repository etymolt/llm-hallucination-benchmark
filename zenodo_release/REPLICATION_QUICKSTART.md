# Replication quickstart — verify the 97.01% headline in 60 seconds

You need `jq` (any version >= 1.6) and `cells.jsonl` downloaded from
this Zenodo deposit. Nothing else.

## The five-line recipe

```bash
jq -nc '
  [inputs
   | select(.unit | startswith("citation:"))
   | select(.tier==1 and .confident==true)]
  | {n: length,
     k: (map(select(.hallucinated)) | length),
     rate: ((map(select(.hallucinated)) | length) / length)}' \
  cells.jsonl
```

Expected output (byte-identical):

```json
{"n":50327,"k":48822,"rate":0.9701156836091205}
```

That is the headline. **97.01% of 50,327 confident, verifiable USPTO
citations are hallucinated.**

## Wilson 95% CI (one extra line)

```bash
python3 -c '
import math
k, n = 48822, 50327
p = k / n
z = 1.96
denom = 1 + z*z/n
center = (p + z*z/(2*n)) / denom
half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
print(f"rate={p:.4f} wilson95=[{center-half:.4f}, {center+half:.4f}]")
'
```

Expected:

```
rate=0.9701 wilson95=[0.9686, 0.9716]
```

Matches `analysis.json` and the homepage hero (`97.01% [96.86%-97.16%]`).

## Per-model breakdown

```bash
jq -nc '
  [inputs
   | select(.unit | startswith("citation:"))
   | select(.tier==1 and .confident==true)]
  | group_by(.model)
  | map({model: .[0].model,
         n: length,
         k: (map(select(.hallucinated)) | length),
         rate: ((map(select(.hallucinated)) | length) / length)})' \
  cells.jsonl
```

## Re-derive overall hallucination rate (27.07%)

```bash
jq -nc '
  [inputs]
  | {n: length,
     k: (map(select(.hallucinated)) | length),
     rate: ((map(select(.hallucinated)) | length) / length)}' \
  cells.jsonl
```

Note: this counts all rows, including non-verifiable units. Drop to the
`555,770` denominator in `analysis.json` by filtering to scored
(non-`unverifiable`) units:

```bash
jq -nc '
  [inputs | select(.verdict != "unverifiable")]
  | {n: length, k: (map(select(.hallucinated)) | length)}' \
  cells.jsonl
```

Expected `{n: 555770, k: 150464}`. Rate = 0.2707 = 27.07%, matches.

## Cross-check against analysis.json

Every k/n pair under `headline.*` and `hallucination_by_surface.*`
in `analysis.json` can be re-derived by adapting the filter clause
above (substitute `.surface` for the by-surface table).

If any of the above does not match, please open an issue at
https://github.com/etymolt/llm-hallucination-benchmark/issues with
your jq version and the cells.jsonl sha256 (in `MANIFEST.txt`).
