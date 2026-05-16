# LLM Brand-Name Hallucination Benchmark — Makefile
#
# Quick reference:
#   make install     # install Python deps
#   make test        # run pytest (catches bugs before burning API credits)
#   make run-smoke   # 10 names × all models × all prompts — sanity check
#   make run-full    # 500 names × all models × all prompts — the real run
#   make aggregate   # produce summary.json from results.csv
#   make publish     # rsync results into the web app for the published article
#   make clean       # nuke results/ — DESTRUCTIVE

PYTHON ?= python3
RESULTS_DIR ?= results
TEST_SET ?= test_set.jsonl
MODELS ?= gpt-5 claude-4.7-opus gemini-3-pro llama-4-maverick
PROMPTS ?= v1_naive v2_constrained v3_grounded
CONCURRENCY ?= 10
WEB_PUBLIC ?= ../../apps/web/public/research

.PHONY: help install test run-smoke run-full aggregate publish clean

help:
	@echo "Targets:"
	@echo "  install     install Python deps from requirements.txt"
	@echo "  test        run pytest (recommend running BEFORE any paid run)"
	@echo "  run-smoke   small sanity-check run (10 names per model)"
	@echo "  run-full    full benchmark run (whole test_set.jsonl)"
	@echo "  aggregate   build summary.json from results.csv"
	@echo "  publish     copy results into apps/web/public/research/"
	@echo "  clean       wipe $(RESULTS_DIR)/ (destructive)"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -v

run-smoke:
	$(PYTHON) runner.py \
		--test-set $(TEST_SET) \
		--models $(MODELS) \
		--prompts $(PROMPTS) \
		--output-dir $(RESULTS_DIR) \
		--concurrency $(CONCURRENCY) \
		--sample 10

run-full:
	$(PYTHON) runner.py \
		--test-set $(TEST_SET) \
		--models $(MODELS) \
		--prompts $(PROMPTS) \
		--output-dir $(RESULTS_DIR) \
		--concurrency $(CONCURRENCY) \
		--yes-costs

aggregate:
	$(PYTHON) aggregator.py \
		--results $(RESULTS_DIR)/results.csv \
		--output $(RESULTS_DIR)/summary.json

publish: aggregate
	@mkdir -p $(WEB_PUBLIC)/llm-hallucination-2026
	cp $(RESULTS_DIR)/results.csv $(WEB_PUBLIC)/llm-hallucination-2026/
	cp $(RESULTS_DIR)/summary.json $(WEB_PUBLIC)/llm-hallucination-2026/
	cp $(RESULTS_DIR)/manifest.json $(WEB_PUBLIC)/llm-hallucination-2026/ 2>/dev/null || true
	cp $(TEST_SET) $(WEB_PUBLIC)/llm-hallucination-2026/
	@echo "Published to $(WEB_PUBLIC)/llm-hallucination-2026/"

clean:
	rm -rf $(RESULTS_DIR)
	@echo "Removed $(RESULTS_DIR)/"
