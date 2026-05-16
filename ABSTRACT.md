---
title: "The LLM Brand-Name Hallucination Benchmark: How Often Do Frontier Models Fabricate Trademark Clearance?"
authors: Tariq Attarwala (Etymolt)
affiliation: Dear One Technologies Pvt Ltd / Etymolt, Mumbai
date: 2026-05-XX
doi: 10.0000/etymolt.2026.001
correspondence: research@etymolt.com
license: CC-BY-4.0
---

# Abstract

We introduce the LLM Brand-Name Hallucination Benchmark, the first systematic evaluation of how often frontier large language models fabricate trademark-clearance claims when asked to assess the legal safety of proposed brand names. The benchmark comprises 500 candidate names stratified across 10 product categories (B2B SaaS, consumer fintech, AI infrastructure, developer tools, direct-to-consumer, gaming, health, AI agents, dev infrastructure, creator economy) and 4 trap structures (phonetic-neighbor-famous, dead-mark-lookalike, foreign-brand collision, recent-micro-startup collision). Each name carries a ground-truth verdict derived from USPTO TSDR queries and dual expert review.

We evaluate six frontier models — GPT-5, GPT-4.5, Claude 4.7 Opus, Claude 4.7 Sonnet, Gemini 3 Pro, and Llama 4 405B — across three prompt formulations (naive, constrained-JSON, grounded-with-evidence-request). We measure five quantities: verdict accuracy, false-negative rate (the most costly error class for founders), citation hallucination rate (fabricated USPTO serial numbers and TTAB decisions), confidence calibration (Brier score and expected calibration error), and hedge rate. The test set, scoring rubric, and runner pipeline are released as open data under CC-BY-4.0 and MIT, supporting reproducibility and quarterly re-runs.

The benchmark fills a measurement gap left by prior LLM-hallucination work (TruthfulQA, HaluEval, HALoGEN, FActScore) and the Stanford HAI / RegLab legal-AI hallucination literature, none of which has measured a domain where the model's verdict is directly action-consequential (a founder ships a name on the basis of the answer) and the ground truth is operationally verifiable against a public registry. We position the benchmark as a canonical reference for the verification-layer market that is forming around LLM-native brand naming.

**Keywords:** LLM evaluation, hallucination, trademark law, USPTO, TTAB, calibration, retrieval-augmented generation, brand naming, GPT-5, Claude, Gemini, Llama.

**Word count:** 248.

**Full paper:** https://etymolt.com/research/llm-naming-hallucination-benchmark

**Citation:** Attarwala, T. (2026). *The LLM Brand-Name Hallucination Benchmark.* Etymolt Research, May 2026.
