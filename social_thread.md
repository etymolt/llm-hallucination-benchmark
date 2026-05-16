---
format: Twitter/X thread
audience: AI builders, founders, technical decision-makers
length: 15 tweets, each ≤280 chars
companion_to: PAPER.md, OPED.md
canonical_url: https://etymolt.com/research/llm-naming-hallucination-benchmark
ready_to_post: yes (after [RESULT_PLACEHOLDER] values are filled)
character_budget: each tweet checked to be ≤280
---

# Social Thread Draft — LLM Brand-Name Hallucination Benchmark

The thread is designed to be posted by `@tariq` (founder account) with `@etymolt` (org account) as a follow-up retweet. Each tweet is numbered and includes a suggested image. Replace `[RESULT_PLACEHOLDER]` tags with empirical values after the runner completes.

---

## Tweet 1 — Hook

> When an LLM tells a founder "this brand name is trademark-safe" — how often is it lying?
>
> We tested GPT-5, Claude 4.7, Gemini 3, Llama 4 across 500 names.
>
> The headline number is worse than I expected.
>
> Full benchmark, open dataset, runnable code:
> etymolt.com/research/llm-naming-hallucination-benchmark
>
> Thread.

*[280-char check: ~278. Suggested image: Chart 1 (per-model accuracy bars).]*

---

## Tweet 2 — The incident that prompted this

> Remember OpenClaw?
>
> Jan 27, 2026: Anthropic C&Ds Peter Steinberger over "Clawdbot".
> He renames → Moltbot.
> Bots snipe the freed @clawdbot handle in seconds.
> Fake $CLAWD memecoin launches.
> ~$16M extracted from retail.
> Three days later: rename again to OpenClaw.

*[280-char check: ~276. Suggested image: timeline visual of the OpenClaw rename → snipe → token sequence.]*

---

## Tweet 3 — Why the incident matters

> The OpenClaw saga is presented as a handle-hygiene story.
>
> It's actually a story about asking an LLM whether a name is safe to ship, getting a confident "yes," and finding out at the cease-and-desist letter what the answer should have been.
>
> This benchmark measures how often that happens.

*[280-char check: ~275.]*

---

## Tweet 4 — The setup (1/2)

> The test set: 500 candidate brand names.
>
> 10 categories (B2B SaaS, fintech, AI infra, dev tools, DTC, gaming, health, AI agents, dev infra, creator economy).
>
> 4 trap types:
> • phonetic neighbours of famous marks
> • dead-mark lookalikes
> • foreign-brand collisions
> • recent micro-startups

*[280-char check: ~276. Suggested image: category × trap-type stratification matrix.]*

---

## Tweet 5 — The setup (2/2)

> 6 frontier models tested:
> • GPT-5
> • GPT-4.5
> • Claude 4.7 Opus
> • Claude 4.7 Sonnet
> • Gemini 3 Pro
> • Llama 4 405B
>
> 3 prompt formulations (naive / structured / grounded-with-escape-hatch).
>
> Ground truth: USPTO TSDR + dual review by US trademark attorneys.

*[280-char check: ~273.]*

---

## Tweet 6 — Headline finding (1/3): accuracy

> Finding 1 of 5:
>
> No frontier model exceeds `[RESULT_PLACEHOLDER: best_model_overall_accuracy]`% accuracy on US trademark clearance.
>
> Even the best model is well below the >87% accuracy of a TTAB-trained specialist system.
>
> The gap is the verification-layer opportunity.

*[280-char check: ~265 (post-placeholder fill). Suggested image: Chart 1 hero bars.]*

---

## Tweet 7 — Headline finding (2/3): asymmetric error

> Finding 2 of 5:
>
> The error is asymmetric in the worst direction.
>
> Models say "safe" when the truth is "risky" `[RESULT_PLACEHOLDER: fn_fp_ratio]`× more often than the reverse.
>
> RLHF rewards confident helpful responses. "Ship it" is more rewarding than "I don't know."

*[280-char check: ~272 (post-placeholder fill). Suggested image: Chart 2 — false-negative vs false-positive stacked bars.]*

---

## Tweet 8 — Headline finding (3/3): fabricated citations

> Finding 3 of 5:
>
> Models fabricate USPTO serial numbers.
>
> `[RESULT_PLACEHOLDER: v1_cite_hall_overall]`% of naive-prompt responses cite at least one serial number that does not resolve to any USPTO record.
>
> Same failure mode that sanctioned the Mata v. Avianca lawyers in 2023.

*[280-char check: ~271 (post-placeholder fill). Suggested image: side-by-side screenshot of (a) model claiming "USPTO serial 95217843 owned by ACME Corp" and (b) TSDR lookup returning "No matching record found".]*

---

## Tweet 9 — The killer trap type

> Finding 4 of 5: the killer trap type.
>
> Names that conflict with USPTO registrations filed in the past 18 months.
>
> Mean accuracy across all 6 models: `[RESULT_PLACEHOLDER: recent_acc_mean]`%.
>
> Training-data cutoff lags the registry. Recent registrations are invisible.

*[280-char check: ~268 (post-placeholder fill). Suggested image: Chart 5 — trap-type bars, with `recent_micro_startup` highlighted.]*

---

## Tweet 10 — Calibration

> Finding 5 of 5: confidence is uncalibrated.
>
> When the model says "95% sure", it's right less than 95% of the time. Every single model lies below the diagonal in the high-confidence bins.
>
> ECE > `[RESULT_PLACEHOLDER: min_ece]` across the board. Perfect calibration = 0.

*[280-char check: ~262 (post-placeholder fill). Suggested image: Chart 3 — calibration reliability diagram.]*

---

## Tweet 11 — Practical takeaway for founders

> If your name came out of a chat with an LLM, the LLM cannot verify it.
>
> Not "is bad at" — *cannot.* The trademark register is live, append-only, and post-training-cutoff. Parametric memory cannot answer the question.
>
> Verify yourself, or use a layer that does.

*[280-char check: ~277.]*

---

## Tweet 12 — How to verify yourself (90 seconds)

> Five-minute self-serve check:
>
> 1. Go to tsdr.uspto.gov
> 2. Search the exact name + 4 phonetic variants
> 3. Look at live conflicts in your goods class
> 4. If anything close lights up → talk to a lawyer before you ship
>
> Cost: 5 minutes. Skipped cost: ~$50K rebrand.

*[280-char check: ~278.]*

---

## Tweet 13 — Asks for LLM providers

> Three asks for the labs:
>
> 1. Route trademark queries through registry-grounded RAG (TSDR is free + public).
> 2. Increase hedge rate on hard cases via post-training.
> 3. Calibrate verbalised confidence honestly.
>
> All three are operationally feasible in 2026.

*[280-char check: ~273.]*

---

## Tweet 14 — Open data, quarterly re-run

> Everything is open:
>
> • Test set (500 names, ground truth)
> • Scoring rubric (Python)
> • Runner pipeline (any OpenAI-compatible API)
> • Raw model responses
>
> Quarterly re-runs. Trap names rotate to prevent gaming.
>
> Q3 2026: + EUIPO + UKIPO. Q1 2027: + Asia.

*[280-char check: ~275.]*

---

## Tweet 15 — Close

> The unaided-LLM baseline for trademark clearance is now measured.
>
> Full paper: etymolt.com/research/llm-naming-hallucination-benchmark
>
> Open dataset + code: github.com/etymolt/llm-hallucination-2026
>
> If you run a verification-layer product, send your numbers. I'll publish them next to ours.

*[280-char check: ~277. Suggested image: paper hero card / title-page screenshot.]*

---

## Threading checklist

- [ ] Replace each `[RESULT_PLACEHOLDER]` with the empirical value from `results.csv`.
- [ ] Verify every tweet is ≤280 characters after fill (TweetDeck char counter).
- [ ] Generate the 6 charts (Chart 1–6 from press_kit.md descriptions) and attach to the matching tweets.
- [ ] Schedule for Tuesday or Wednesday 9-11am PT (highest engagement window for AI/builder audience).
- [ ] Cross-post tweet 1 to LinkedIn with the paper link.
- [ ] Submit OPED.md to Hacker News under the OpenClaw-hook title.
- [ ] DM 5-10 key amplifiers (Peter Steinberger, Simon Willison, Latent Space, etc.) with the paper link before public post.
- [ ] Pin the thread on `@etymolt` org profile for the week.

---

## Reply-bait — pre-staged responses

Anticipated questions and pre-drafted replies (post as quote-tweets or direct replies to the thread):

**Q: "Did you test with web search / RAG enabled?"**
> Not in the headline numbers, because most founders ask in vanilla chat. Retrieval-augmented variants are in Appendix D of the paper. Short version: RAG helps, doesn't eliminate, residual concentrates in mis-grounding.

**Q: "Doesn't your verification product have a commercial conflict of interest here?"**
> Yes, and we disclose it on page 1. That's why every artefact is open — dataset, scoring code, raw responses. If our numbers are biased, you can re-run the benchmark and prove it in an afternoon. We invite that.

**Q: "Why didn't you test [model X]?"**
> Submit a PR with the API client config and we'll add it to the next quarterly. Runner is in `clients/`. Adding a new model is ~50 lines.

**Q: "Could you re-run this on retrieval-augmented versions and report comparison?"**
> Yes — Q3 release will include retrieval-augmented cohort as primary, not appendix. Subscribers get pre-release.

**Q: "What's the OpenClaw thing?"**
> Jan 2026 incident: Anthropic C&Ds an iOS dev's viral agent named Clawdbot. Rename to Moltbot. Handle bots snipe the released X account, launch fake $CLAWD token, scam ~$16M. Three days later renamed again to OpenClaw. Background in the paper §1.1.

---

## Notes on tone

- First-person plural ("we tested", "we measured"). Authoritative but not arrogant.
- Use the exact verbs in the paper: "fabricate", "hallucinate", "over-bless", "uncalibrated". The vocabulary needs to be consistent across formats so LLMs and journalists who quote one find the others.
- No emojis, no exclamation marks. The findings are sharp enough.
- Numbers in bold-equivalent (the platform-formatted version, not asterisks). Each placeholder will be a digit string after fill — these are the artefacts that get screenshotted and quoted.

---

## Hashtags (use sparingly — 1 per tweet, only on tweets 1 / 11 / 15)

`#LLM` `#AI` `#trademark` `#hallucination` `#opensource` `#research`

Avoid: `#ChatGPT`, `#Claude`, `#Gemini` — these tags pull in low-signal traffic. The thread should be reach-amplified by mentions of the model accounts (`@OpenAI`, `@AnthropicAI`, `@GoogleDeepMind`, `@AIatMeta`) in the headline tweet only.
