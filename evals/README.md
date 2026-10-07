# TrialScout summary evals (promptfoo)

Tests whether an LLM can write faithful, plain-language summaries of PubMed abstracts.
The test data is 9 real papers from TrialScout's `demo_cache.json` plus one "no abstract" edge case.

## Run it
```bash
cd ~/Desktop/trialscout-evals
export ANTHROPIC_API_KEY=your-key      # type it yourself in this Terminal window; never save it in a file
bash run.sh                            # runs the eval, then opens the results grid
```
Or step by step: `npx promptfoo@latest eval` then `npx promptfoo@latest view`.

## What is being compared
Three prompts (v3, v4, v5) on Claude Haiku 4.5, 10 test cases each = 30 results.
v1 and v2 are earlier baselines, commented out in `promptfooconfig.yaml`.

## The checks (metric names in the results grid)
- `short-enough`: 60 words or fewer
- `no-hype`: no words like "breakthrough" or "cure"
- `no-markdown-header`: no "# Heading" at the start
- `no-invented-numbers`: every number in the summary appears in the abstract (rounding is allowed)
- `faithful`: LLM-graded, needs a score of 0.8 or higher
- `plain-language`: LLM-graded, needs a score of 0.7 or higher

## How to read the results
- Compare average scores across prompts, not just the pass count. The LLM grader is not perfectly repeatable.
- Click a failing cell to see which check failed and the grader's reason.
- Change one thing in a prompt, rerun, and watch which cells flip.
