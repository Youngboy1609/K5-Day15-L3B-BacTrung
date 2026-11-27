# Helpful-vote weighting design

## Goal

Use Shopee's per-review “Hữu ích” vote count as a bounded signal when computing the phone-case review score, without asking the model to infer that count or changing CP2's locked evaluation metrics.

## Data contract

- Review source data may contain optional `helpful_count`: a non-negative integer copied from the review's helpful-vote count.
- The local CP2 fixtures are synthetic. Any fixture vote counts are illustrative synthetic values, not scraped Shopee data or evidence of user behavior.
- Missing/null count is neutral (`0` votes for weighting purposes) and must not be guessed.
- Sentiment and evidence-strength judging must not use vote count; popularity must not change what a review says.

## Weight calculation

For a known count `n`, use a bounded logarithmic multiplier:

`helpfulness_factor(n) = 1 + min(log1p(n) / log1p(10), 1)`

Thus 0 votes gives `1.0`, 10 votes gives `2.0`, and counts above 10 remain capped at `2.0`. Missing values use `1.0`.

Per-review aggregation weight becomes:

`star_population_weight × evidence_strength_weight × helpfulness_factor`

This preserves star-stratified sampling and evidence-strength weighting while allowing reviews with more helpful votes to influence the aggregate more. Evidence ordering should use the same combined weight so visible citations are consistent with the aggregate. The capped factor limits popularity bias; the vote count is a relevance signal, not proof that a review is true.

## Scope and risks

- Current demo still reads only local fixtures. No Shopee fetching/scraping or API integration is added.
- Do not change `eval/metric_spec.yaml` or the CP2 acceptance threshold, which are locked. Record this post-CP2 behavior change in `spec.md` §10 and explain it in §4.
- A real-data integration must preserve provenance and verify the platform actually exposes the count for the collected review. Vote counts can be biased by review age/exposure, so keep the multiplier bounded.
- Missing data is neutral, never a zero-quality judgment.

## Verification

- Unit-test the multiplier at 0, intermediate counts, 10, and above 10.
- Unit-test that missing counts are neutral and larger counts cannot reduce a review's aggregation weight.
- Run the full agent tests, survey-analysis tests, `python -B run.py check`, and `git diff --check`.
