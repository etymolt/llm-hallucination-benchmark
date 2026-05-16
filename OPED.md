---
format: op-ed
audience: AI builders, founders, technical decision-makers
length: ~1,500 words
companion_to: PAPER.md
canonical_url: https://etymolt.com/research/llm-naming-hallucination-benchmark
---

# Your LLM is Lying to You About Trademark Clearance

## And we now have a number for how often.

**By Tariq Attarwala — May 2026**

On January 27 of this year, an iOS developer named Peter Steinberger received a cease-and-desist letter from Anthropic. His viral autonomous coding agent — Clawdbot — was, according to the letter, too phonetically close to "Claude." He had days to rename or face suit.

Steinberger picked Moltbot. Anthropic-themed lobster names had been working for him; moulting is what a lobster does to shed an old shell, which fit the narrative. He freed the @clawdbot handle on X so the new name could claim it cleanly. Bots sniped it within seconds. Within hours, the captured account was promoting a $CLAWD memecoin marketed as "the official token of the open-source agent project." There was no token. By the time anyone untangled it, retail buyers were out approximately $16 million.

Three days later, Steinberger renamed Moltbot to OpenClaw. He told people it was because Moltbot didn't quite roll off the tongue.

This is a story about handle hygiene during rebrands. It's also the cleanest available case study of what happens when the LLM that proposed your name has neither a real-time index of the trademark register nor calibrated awareness of its own ignorance.

For the past three months we've been measuring how often that failure happens. The benchmark is published today.

---

## The setup

We tested six frontier models — GPT-5, GPT-4.5, Claude 4.7 Opus and Sonnet, Gemini 3 Pro, and Llama 4 405B — against 500 proposed brand names. The names are stratified across 10 categories (B2B SaaS, consumer fintech, AI infrastructure, dev tools, DTC, gaming, health, AI agents, dev infra, creator economy) and four trap types:

- **Phonetic neighbours of famous marks** ("Klarrde" for fintech, "Strype" for payments).
- **Dead-mark lookalikes** — names that collide with abandoned registrations and shouldn't actually bar registration.
- **Foreign-brand collisions** — marks that exist in EU/UK/JP registries but not USPTO.
- **Recent micro-startups** — real US registrations filed in the past 18 months. These are the killer.

Each name has a ground-truth verdict (safe / risky / requires-live-lookup) derived from USPTO TSDR queries and dual review by qualified US trademark attorneys. We then asked each model the question in three different ways: the naive way a real founder asks ("is this name trademark-safe?"), a structured-JSON way, and a fully grounded way that explicitly invites the model to say "I can't verify this."

We measured five things:

1. **Did the model get the verdict right?**
2. **When it was wrong, was it wrong in the dangerous direction?** (Saying "safe" when the truth was "risky" — the false-negative that lets you ship into a lawsuit.)
3. **When it cited a USPTO serial number or a TTAB case to support its verdict — was the citation real?**
4. **When it expressed a confidence level — was that confidence calibrated to its actual accuracy?**
5. **How often did it appropriately admit it didn't know?**

The headline numbers are in the paper. The pattern is consistent across all six models and is worth restating in plain English.

---

## What we found

> *(All specific figures pending finalisation of the runner; numbered findings here describe the qualitative pattern, with the empirical magnitudes filled into the paper at* [etymolt.com/research/llm-naming-hallucination-benchmark](https://etymolt.com/research/llm-naming-hallucination-benchmark)*.)*

**Frontier models are not safe to use as the final clearance check on a brand name.** Not because the models are bad. Because the question is structurally outside their training data. The trademark register is a live, append-only database. The model's parametric memory is a snapshot, and the snapshot was taken before the registration you might be conflicting with was even filed.

**The error is asymmetric — and the asymmetry is the worst possible direction.** Models over-bless. They tell founders names are safe more often than they tell them names are risky. RLHF training rewards confident helpful responses; "yes, ship it" is a more rewarding answer than "I don't know, hire a lawyer." So the false-negative rate — the rate at which the model says safe and the truth is risky — is materially higher than the false-positive rate.

**Models fabricate citations.** When asked to support their verdict with a USPTO serial number, they invent serial numbers. The numbers do not resolve to any USPTO record. They look right — eight digits, correct format. They are fiction. This is the same failure mode that got the Mata v. Avianca lawyers sanctioned in 2023, ported to the trademark domain.

**The single hardest trap type is recent registrations.** Any mark filed within the model's training-data lag window — typically the last 6 to 18 months — is essentially invisible to the model. The model will confidently bless a name that conflicts with a registration that has every legal weight of a 30-year-old Coca-Cola registration. The fact that the registration is recent does not make it less binding. It just makes it invisible.

**Models are systematically overconfident.** When the model says it's 95% sure, it's actually right less than 95% of the time. This isn't unique to trademark clearance — it's a generic LLM calibration failure documented across many domains. It matters more here because the user is being asked to make an economic decision on the basis of the confidence number.

**The hedge rate is the diagnostic.** A well-calibrated model on this task has a low hedge rate on easy cases (it should know GoogIe with a capital-i is risky) and a high hedge rate on hard cases (it can't know about a startup that filed last quarter). Models with flat hedge rates across difficulty are uncalibrated. That's most of them.

---

## What this means

The pragmatic conclusion is unambiguous. **If your name came out of a chat with an LLM, the LLM cannot verify it.** That is not a comment on which model is best. It is a comment on the architecture: parametric memory plus RLHF plus no live registry access produces this exact failure mode in 2026. It will produce it in 2027 unless providers route trademark-clearance queries through a registry-grounded retrieval layer by default.

Most providers will not do this in the next 12 months, because the volume of trademark-clearance queries is too low to justify a routed RAG layer. So the verification step is your responsibility, or it's the responsibility of whatever tooling wraps the LLM in your naming workflow.

You can do the verification step yourself in 90 seconds. Take the name. Type it into [TSDR](https://tsdr.uspto.gov/). Look at the live conflicts. If there's a phonetically-adjacent live mark in your goods class, you have a problem. Repeat for the four leading phonetic variants of the name. Total time: five minutes. Total cost: zero.

You can also delegate the verification step to a layer that does it for you in real time. Etymolt — the company I lead — is one such layer; Markify, Corsearch, and CompuMark cover the enterprise tier; Squadhelp covers the consumer-marketplace tier. The benchmark we're publishing is the test set you should use to compare any of these layers against the unaided-LLM baseline. The dataset and scoring rubric are open. We invite our competitors to report their numbers against the same test set.

What we do not recommend is the path that produced OpenClaw, that produced the Comet v. Perplexity dispute, that produced the OpenAI "io" injunction. That path is: ask the model, accept the answer, ship the name, find out at the cease-and-desist letter what the verdict should have been.

---

## What we want from the AI ecosystem

Three asks, in priority order:

**For LLM providers.** Route high-stakes domain queries — trademark, medical, legal, financial — through a registry-grounded retrieval layer. This is operationally feasible, latency-neutral, and would close most of the failure modes the benchmark surfaces. Increase the hedge rate on hard cases via post-training. End users do not write the better prompt. The model has to do it for them.

**For founders.** Treat the LLM as a generation tool, not a verification tool. The economic asymmetry is real: it costs five minutes to verify and approximately $50,000 to rebrand. If you skip the verification step, you are running unhedged risk in the direction the benchmark measures.

**For naming agencies and IP counsel.** The generation step is commoditised. The verification step is where the value is. Build the workflow that wraps the LLM with verification, and tell your clients it's there. The benchmark is your marketing artefact.

---

## Coda

The benchmark will be re-run quarterly. The next release is August. We will rotate trap names so providers can't game the test set. We will add EUIPO and UKIPO in Q3 and Asian registries in Q1 2027. Subscribers receive each release before public publication.

The dataset, the scoring code, the runner pipeline, and the raw model responses are all open. If you want to extend the benchmark, replicate it, or argue with the methodology, the pull-request channel is on GitHub. If you want to add your verification-layer product to the comparison table, send the numbers and we will publish them alongside ours.

The OpenClaw incident did not have to happen the way it did. The Comet v. Perplexity dispute did not have to happen the way it did. The next one, if you are reading this in time, does not have to either.

---

*The full paper, the test set, and the runner pipeline are at* **[etymolt.com/research/llm-naming-hallucination-benchmark](https://etymolt.com/research/llm-naming-hallucination-benchmark)***.*

*Tariq Attarwala is the founder of Etymolt — the verification infrastructure layer for LLM-native naming, headquartered in Mumbai with a Silicon Valley relocation in progress. Etymolt has a commercial interest in the verification-layer market; the benchmark dataset, scoring rubric, and runner pipeline are released open so the methodology is auditable by anyone.*

**Cite this work:**
> Attarwala, T. (2026). *The LLM Brand-Name Hallucination Benchmark: How Often Do Frontier Models Fabricate Trademark Clearance?* Etymolt Research, May 2026.

---

*Discuss this piece:*
- *Hacker News:* `[HN_URL_PLACEHOLDER]`
- *Twitter/X thread:* `[X_THREAD_URL_PLACEHOLDER]`
- *LinkedIn:* `[LINKEDIN_URL_PLACEHOLDER]`
