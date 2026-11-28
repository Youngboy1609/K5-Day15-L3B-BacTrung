# Staged Review UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the single-screen review demo into an honest three-stage flow where users inspect locally available exact-variant reviews before starting AI analysis.

**Architecture:** Add a read-only `POST /preview` route in the existing local HTTP app that reuses `get_product_reviews` and returns a minimal projection of the exact deterministic sample. The browser moves through product selection, review preview, and analysis/result states; it keeps the preview visible during the real `/analyze` request. The existing analysis endpoint, agent behavior, and benchmark artifacts remain unchanged.

**Tech Stack:** Python standard-library HTTP server, vanilla HTML/CSS/JavaScript, `unittest`, existing optional Playwright browser tests.

---

## File map

- Modify `codebase/app.py`: add `/preview`, validate the same three request fields as `/analyze`, reuse the existing lookup/sampling implementation, and project only preview-safe fields.
- Modify `codebase/web/index.html`: add a clear step indicator, stage containers, preview controls, and an analysis status region while retaining existing result/error semantics.
- Modify `codebase/web/app.js`: manage stage transitions, request preview, render safe review text, expand/collapse the preview, run analysis, and handle back/retry/stale responses.
- Modify `codebase/web/styles.css`: add restrained stage/progress and review-list styles while preserving design tokens, focus styles, reduced motion, and responsive behavior.
- Modify `tests/test_app.py`: cover preview endpoint success, exact filtering, projection, invalid inputs, and no-local-data outcomes.
- Modify `tests/test_web.py`: cover the staged flow, preview while analysis is pending, errors/back/retry, keyboard behavior, and responsive layout.
- Do not modify `codebase/agent.py`, `codebase/ai.py`, `codebase/tools.py`, collector crawling behavior, benchmark/metric/run artifacts, or cost files.

## Task 1: Define and test the preview API contract

**Files:**
- Modify: `tests/test_app.py`
- Modify: `codebase/app.py`

- [x] **Step 1: Write failing endpoint tests**

Add tests using the existing `app.make_server(port=0)` test fixture. A valid request to `POST /preview` for the clear-case fixture, iPhone 15 Pro, and exact variant must return JSON containing `status: "ok"`, a source label/type, product/model/variant context, coverage counts, and a `reviews` list. Each review must contain only `review_id`, `stars`, `text`, and a media summary; it must not expose file paths, media source URLs, helpful counts, or unrelated review fields. Check every returned ID against the exact phone model and exact variant in `data/reviews.json`.

Also assert that an unknown product returns the existing `NO_LOCAL_DEMO_DATA` code without review rows, a non-existent variant returns `VARIANT_NOT_FOUND` without review rows, and malformed/extra request fields are rejected consistently with `/analyze`.

- [x] **Step 2: Run the focused tests and confirm failure**

Run: `python -B -m unittest discover -s tests -p test_app.py`

Expected: the new preview tests fail because `POST /preview` is not implemented.

- [x] **Step 3: Implement the minimal preview route**

In `codebase/app.py`, import `get_product_reviews` from `tools`. Refactor only shared request parsing/shape validation if needed so `/preview` and `/analyze` accept exactly `product_url`, `phone_model`, and `case_variant`. For `POST /preview`, call:

```python
lookup = get_product_reviews(
    request["product_url"],
    request["phone_model"],
    request["case_variant"],
)
```

For non-`ok` lookup results, return the existing typed error fields with no review rows. For success, return a projection with source metadata, product/model/variant, `review_count`, `eligible_count`, `sample_limit`, `sample_seed`, and reviews containing only ID, stars, text, and media count/types. Do not return a crawl status or any claim that Shopee was accessed. Keep `/analyze` request/response behavior unchanged.

- [x] **Step 4: Run API tests and the existing server tests**

Run: `python -B -m unittest discover -s tests -p test_app.py`

Expected: all preview and existing API tests pass.

Run: `python -B -m unittest discover -s tests`

Expected: existing application tests pass; optional Playwright tests may skip only when their browser dependency is unavailable.

- [x] **Step 5: Commit the API contract**

```text
git add codebase/app.py tests/test_app.py
git commit -m "feat: add exact-match review preview endpoint"
```

## Task 2: Add the three-stage browser flow

**Files:**
- Modify: `tests/test_web.py`
- Modify: `codebase/web/index.html`
- Modify: `codebase/web/app.js`

- [x] **Step 1: Write browser-flow tests**

Update the Playwright helper so it first chooses a demo listing, advances to preview, and then explicitly starts analysis. Add assertions that:

1. Product form is stage 1 and preview/result are initially hidden.
2. Advancing calls `/preview`, shows exact-match coverage and review text, and changes the visible step to review preview.
3. Starting analysis leaves the actual preview visible while `/analyze` is delayed by a test route; the status says AI is analyzing the displayed reviews, not crawling.
4. Once `/analyze` returns `status: "ok"`, the result stage shows the existing recommendation, coverage, evidence, advice, and expandable details.
5. The review expand/collapse action works and uses text content safely.

Run: `python -B -m unittest discover -s tests -p test_web.py`

Expected: FAIL because the staged markup and state management do not exist.

- [x] **Step 2: Add accessible stage markup**

In `index.html`, add a semantic ordered step indicator and separate product, preview, and result sections. Keep labels and error IDs associated with their existing inputs. Add preview source/coverage text, a review list, expand/collapse button, back button, and a distinct analysis button. Keep the current result section content and error-feedback region; do not duplicate analysis data in markup.

- [x] **Step 3: Implement preview and stage transitions**

In `app.js`, keep one explicit stage value in state (`product`, `preview`, or `result`) and use a request version counter to ignore stale preview/analysis responses. On advancing from valid product selection, POST the three fields to `/preview`. Render only returned data using `textContent`/DOM nodes (never interpolate review text into `innerHTML`). If preview reports no product/variant/data, stay in the flow and show a correction message without a recommendation.

On the preview stage, show at most five review rows by default and toggle the remainder using a labelled button. Starting analysis sends the same selected fields to the unchanged `/analyze` endpoint. While the request is pending, keep the preview visible, disable duplicate analysis submissions, and announce one factual status. On success transition to the existing result rendering. On failure keep the preview available and show retry/back controls. Back navigation returns to product selection without showing stale results.

- [x] **Step 4: Run staged flow checks**

Run: `python -B -m unittest discover -s tests -p test_web.py`

Expected: browser tests pass or skip only for a missing optional Playwright browser; no new failures.

- [x] **Step 5: Commit the staged browser flow**

```text
git add codebase/web/index.html codebase/web/app.js tests/test_web.py
git commit -m "feat: add staged review preview and analysis flow"
```

## Task 3: Style and verify responsive/accessibility behavior

**Files:**
- Modify: `codebase/web/styles.css`
- Modify: `tests/test_web.py`

- [x] **Step 1: Add visual-state assertions**

Add browser checks for the visible step indicator, focus after stage changes, disabled/loading analysis button state, and no horizontal overflow at 320, 375, 414, and 768 pixels. Assert the reduced-motion preference suppresses non-essential transitions.

- [x] **Step 2: Style the staged UI**

Add CSS using existing custom properties and conventions. Make stage status visually clear without a fake percentage or looping spinner. Keep the review list compact, with readable wrapped text, star values plus text labels, media availability text, and a progressive disclosure control. Keep the preview and primary action reachable on mobile; do not auto-scroll users while reviews are being displayed. Add only restrained transitions and honor `prefers-reduced-motion`.

- [x] **Step 3: Run browser and app regression checks**

Run:

```text
python -B -m unittest discover -s tests -p test_web.py
python -B -m unittest discover -s tests
python -B run.py check
```

Expected: browser and application tests pass (apart from documented optional skips), `run.py check` reports the unchanged 24 benchmark cases, and no benchmark/run/cost artifact is modified.

- [x] **Step 4: Perform visual smoke**

Start `python -B run.py` with the fake model provider and use the existing local browser tooling to inspect desktop and mobile widths. Verify:

- product → preview → analysis/result is understandable without narration;
- actual preview rows remain visible while the delayed model response is pending;
- the source label clearly says local fixture or collector export;
- no message implies a live Shopee crawl;
- no horizontal scroll, clipped controls, or forced scroll jump occurs.

- [x] **Step 5: Commit the UI styling and verification fixes**

```text
git add codebase/web/styles.css tests/test_web.py
git commit -m "style: refine staged review workflow"
```

## Completion criteria

- Preview shows only the exact deterministic review sample from the local lookup helper.
- AI analysis remains opt-in and uses the existing `/analyze` behavior.
- The preview remains on screen during the actual analysis request.
- Error, retry, back, keyboard, reduced-motion, and mobile states are covered.
- No live Shopee crawl, fake crawl event, agent/model change, benchmark change, or cost change is introduced.

## Execution record

- API regression suite: 20 tests passed.
- Full application suite with `MODEL_PROVIDER=fake`: 43 tests passed, 1 optional Playwright test class skipped because the Python Playwright dependency is unavailable.
- Interactive browser smoke using the available browser tool: product → preview → analysis/result, review expansion/collapse, preview retained during a deferred analysis response, and widths 320/375/414/768 checked without horizontal overflow.
- Benchmark check: 24 cases remain unchanged and valid.
