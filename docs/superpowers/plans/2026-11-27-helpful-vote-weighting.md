# Helpful-vote weighting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the optional Shopee “Hữu ích” count as a bounded multiplier in review weighting.

**Architecture:** The count is source metadata on each review, not a model judgment. The agent computes a capped logarithmic multiplier and combines it with the existing star-population and evidence-strength weights. Missing counts remain neutral; vote counts do not alter sentiment classification.

**Tech Stack:** Python standard library, JSON fixtures, `unittest`.

---

### Task 1: Define and test the helpful-vote multiplier

**Files:**
- Modify: `tests/test_agent.py`
- Modify: `codebase/agent.py`

- [ ] **Step 1: Add failing multiplier tests**

Add `from agent import _helpfulness_factor` to the imports in `tests/test_agent.py`, then add:

```python
def test_helpfulness_factor_is_neutral_at_zero_and_caps_at_two(self):
    self.assertEqual(_helpfulness_factor(0), 1.0)
    self.assertGreater(_helpfulness_factor(5), 1.0)
    self.assertEqual(_helpfulness_factor(10), 2.0)
    self.assertEqual(_helpfulness_factor(50), 2.0)
    self.assertEqual(_helpfulness_factor(None), 1.0)
```

Import `_helpfulness_factor` alongside `answer`.

- [ ] **Step 2: Run the targeted test and verify it fails**

Run: `python -B -m unittest discover -s tests -p test_agent.py -v`

Expected: failure because `_helpfulness_factor` is not defined yet.

- [ ] **Step 3: Implement the bounded multiplier**

Add `import math` and:

```python
def _helpfulness_factor(helpful_count):
    if helpful_count is None:
        return 1.0
    if not isinstance(helpful_count, int) or isinstance(helpful_count, bool) or helpful_count < 0:
        raise ValueError("helpful_count must be a non-negative integer or None")
    return 1.0 + min(math.log1p(helpful_count) / math.log1p(10), 1.0)
```

- [ ] **Step 4: Re-run the targeted test**

Run: `python -B -m unittest discover -s tests -p test_agent.py -v`

Expected: PASS.

### Task 2: Integrate source vote counts into review aggregation

**Files:**
- Modify: `data/reviews.json`
- Modify: `codebase/agent.py`
- Modify: `tests/test_agent.py`

- [ ] **Step 1: Add synthetic fixture counts**

Add an integer `helpful_count` to every fixture review. Use explicitly illustrative values (for example 0, 2, 5, 10); keep the dataset card clear that these are synthetic and not collected from Shopee.

- [ ] **Step 2: Add a failing weighted-score test**

Add `from agent import _weighted_score` and:

```python
def test_helpful_votes_increase_relative_score_weight_and_missing_is_neutral(self):
    reviews = [
        {"review_id": "positive", "stars": 5, "helpful_count": 10},
        {"review_id": "negative", "stars": 5, "helpful_count": 0},
    ]
    judgements = {
        "positive": {"sentiment": "positive", "evidence_strength": "medium"},
        "negative": {"sentiment": "negative", "evidence_strength": "medium"},
    }
    score = _weighted_score(reviews, judgements, {"5": 2}, {"5": 2})
    self.assertGreater(score, 0)

    reviews[0]["helpful_count"] = None
    neutral_score = _weighted_score(reviews, judgements, {"5": 2}, {"5": 2})
    reviews[0]["helpful_count"] = 0
    zero_vote_score = _weighted_score(reviews, judgements, {"5": 2}, {"5": 2})
    self.assertEqual(neutral_score, zero_vote_score)
```

- [ ] **Step 3: Apply the multiplier in `_weighted_score`**

For each review compute the multiplier (or `1.0` for a missing count) and weight:

```python
helpfulness_factor = _helpfulness_factor(review.get("helpful_count"))
weight = population_weight * strength * helpfulness_factor
```

Do not add `helpful_count` to the model's sentiment/evidence-strength judgement contract. Include count and multiplier in the output `review_assessments` and citations so the weighting is inspectable. Rank displayed evidence by combined influence, while retaining the existing preference to show both negative and positive evidence.

- [ ] **Step 4: Run targeted and full tests**

Run: `python -B -m unittest discover -s tests -v`

Expected: all agent and survey-analysis tests pass.

### Task 3: Document the post-CP2 change and verify repository checks

**Files:**
- Modify: `spec.md`
- Modify: `data/DATA_CARD.md`
- Modify: `README.md`

- [ ] **Step 1: Document the score factor**

Update §4 with the source field and formula; state that mock fixture values are synthetic and that actual Shopee collection remains unverified. Add a post-CP2 changelog entry. Do not edit §7 thresholds or `eval/metric_spec.yaml`.

- [ ] **Step 2: Update data and demo notes**

Document that `helpful_count` values in the local fixture are synthetic and that missing count is neutral. Update the demo output description to show the count and bounded multiplier.

- [ ] **Step 3: Run final verification**

Run:

```text
python -B -m unittest discover -s tests -v
python -B run.py check
git diff --check
```

Expected: all tests pass, the checker still reports 10 benchmark rows / 4 user-sourced rows / 3 metrics, and there are no whitespace errors. The existing CP3 warning about needing 20–30 benchmark rows is expected at CP2.
