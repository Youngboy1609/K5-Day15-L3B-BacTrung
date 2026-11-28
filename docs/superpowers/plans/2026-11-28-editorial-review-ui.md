# Editorial Review UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make BacTrung’s existing product → exact-variant preview → result flow read like one polished editorial review experience without changing its data or analysis behavior.

**Architecture:** Keep the current vanilla HTML/CSS/JS structure, endpoints, DOM IDs used by `app.js`, and stage controller. Add semantic layout wrappers in the existing HTML, style the existing review/result content with the approved paper/teal tokens, and verify the unchanged interactions through the existing browser tests.

**Tech Stack:** HTML, CSS custom properties, vanilla JavaScript, Python `unittest`, Playwright browser tests.

---

## File map

- Modify `codebase/web/index.html`: organize the existing product form, preview, and result into editorial main/aside regions; preserve all IDs and labels consumed by `app.js` and `tests/test_web.py`.
- Modify `codebase/web/styles.css`: implement page hierarchy, reading measure, contextual panels, evidence grouping, and responsive reflow using existing color tokens.
- Modify `tests/test_web.py`: add regression checks for the three layout regions while retaining existing behavior checks for sample counts, source, exact-variant evidence, transitions, retries, and product changes.
- Do not modify `codebase/web/app.js`, `codebase/app.py`, model code, APIs, evaluation/cost/trace artifacts, or other team-owned files unless a test proves a strictly necessary accessible-state hook is missing. Current runtime already renders all required real values safely.

## Task 1: Add failing structural regression tests

**Files:**
- Modify: `tests/test_web.py`

- [ ] **Step 1: Add a test for the approved editorial regions**

Add this test inside `WebDemoTests`:

```python
def test_editorial_regions_exist_across_all_three_stages(self):
    expect(self.page.locator("#product-layout")).to_be_visible()
    self.page.get_by_role("button", name="Dùng mẫu demo").click()
    with self.page.expect_response(lambda response: response.url.endswith("/preview")):
        self.page.get_by_role("button", name="Xem review khớp mẫu").click()
    expect(self.page.locator("#preview-layout")).to_be_visible()
    expect(self.page.locator("#preview-source")).to_contain_text("fixture")
    with self.page.expect_response(lambda response: response.url.endswith("/analyze")):
        self.page.get_by_role("button", name="Phân tích 8 review").click()
    expect(self.page.locator("#result-layout")).to_be_visible()
    expect(self.page.locator("#recommendation")).to_contain_text("Cần xem xét thêm")
    expect(self.page.locator(".evidence-item")).to_have_count(3)
```

- [ ] **Step 2: Run the test and verify it fails on the missing layout hook**

Run: `$env:MODEL_PROVIDER='fake'; python -B -m unittest tests.test_web.WebDemoTests.test_editorial_regions_exist_across_all_three_stages`

Expected: failure because `#product-layout`, `#preview-layout`, and `#result-layout` do not exist yet. It must not fail on a server error or fixture mismatch.

- [ ] **Step 3: Add a desktop/mobile grid regression test**

Add this test in `WebDemoTests` before changing the markup or styles:

```python
def test_result_layout_uses_two_columns_on_desktop_and_one_on_mobile(self):
    self.page.set_viewport_size({"width": 768, "height": 1000})
    self.page.get_by_role("button", name="Dùng mẫu demo").click()
    self.analyze()
    layout = self.page.locator("#result-layout")
    expect(layout).to_be_visible()
    columns = lambda: layout.evaluate(
        "element => getComputedStyle(element).gridTemplateColumns.trim().split(/\\s+/).length"
    )
    self.assertEqual(columns(), 2)
    for width in (320, 375, 414, 768):
        self.page.set_viewport_size({"width": width, "height": 1000})
        overflow = self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
        self.assertFalse(overflow, f"horizontal overflow at {width}px")
        expect(layout).to_be_visible()
        if width <= 640:
            self.assertEqual(columns(), 1)
```

- [ ] **Step 4: Run both new tests and verify the expected red state**

Run: `$env:MODEL_PROVIDER='fake'; python -B -m unittest tests.test_web.WebDemoTests.test_editorial_regions_exist_across_all_three_stages tests.test_web.WebDemoTests.test_result_layout_uses_two_columns_on_desktop_and_one_on_mobile`

Expected: failures only because layout wrappers are missing (and therefore no desktop grid exists). No server or fixture errors.

## Task 2: Group the existing three stages semantically

**Files:**
- Modify: `codebase/web/index.html`
- Test: `tests/test_web.py`

- [ ] **Step 1: Wrap existing product fields without changing control IDs**

Inside `#analyze-form`, group the existing URL, demo, model, variant, action, and status controls with this layout:

```html
<div id="product-layout" class="product-layout">
  <div class="product-fields">
    <!-- Keep the existing labeled URL field, demo button, model field,
         variant field, submit action, and form status unchanged here. -->
  </div>
  <aside class="product-note" aria-label="Thông tin về dữ liệu">
    <p class="section-label">Đọc đúng mẫu</p>
    <p>Chỉ dùng review từ dữ liệu cục bộ khớp link, dòng máy và biến thể. Demo không truy cập Shopee.</p>
  </aside>
</div>
```

Keep the required inputs, labels, `aria-describedby`, help/error nodes, and every `id` exactly as currently referenced by JavaScript and tests. Avoid duplicating the existing local-data disclaimer: replace its old wording with a concise field-specific explanation, and keep the aside note about exact matching.

- [ ] **Step 2: Group preview and result content while preserving content order**

Wrap the preview list and its expand control in `#preview-layout.preview-layout`, and wrap result recommendation/coverage/advice and evidence in `#result-layout.result-layout`. Keep the result DOM reading order as verdict → coverage/source note → evidence → buyer advice → expandable details; retain the existing IDs and `details` disclosure.

- [ ] **Step 3: Run structural and existing stage tests**

Run: `$env:MODEL_PROVIDER='fake'; python -B -m unittest tests.test_web.WebDemoTests.test_editorial_regions_exist_across_all_three_stages tests.test_web.WebDemoTests.test_result_layout_uses_two_columns_on_desktop_and_one_on_mobile tests.test_web.WebDemoTests.test_preview_and_result_are_separate_stages_and_preview_stays_during_analysis tests.test_web.WebDemoTests.test_preview_can_expand_and_collapse_review_sample`

Expected: structural and existing stage tests pass; the grid regression is still red only because the HTML wrappers are not styled yet.

## Task 3: Apply the editorial hierarchy and responsive layout

**Files:**
- Modify: `codebase/web/styles.css`
- Test: `tests/test_web.py`

- [ ] **Step 1: Style the product-selection split**

Add rules using existing palette/spacing tokens:

```css
.product-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(15rem, 0.65fr);
  gap: var(--space-xl);
  align-items: start;
}

.product-fields { display: grid; gap: var(--space-lg); min-width: 0; }

.product-note {
  border-inline-start: 3px solid var(--color-accent);
  padding: var(--space-md);
  background: var(--color-accent-soft);
}
```

Keep form fields full-width inside their column and do not reduce current minimum control sizes.

- [ ] **Step 2: Style preview as an editorial reading surface**

Style `.preview-layout` as a main review column with a restrained context column at wide sizes. Make each `.preview-item` read as an entry: clear rating/review-ID metadata, generous text measure, and a distinct media note. Keep source and real counts visible, preserve the existing expansion action, and do not crop or truncate review text.

- [ ] **Step 3: Style result as verdict plus evidence**

Style `.result-layout` as a dominant recommendation/coverage/advice column and a readable evidence column. Give evidence items separate surfaces or strong typographic grouping using the existing `--color-*` tokens. Keep recommendation status text visible and maintain the role label, rating/ID, quote, and reason for every evidence item.

- [ ] **Step 4: Add narrow-screen reflow**

Within the existing `@media (max-width: 40rem)` block, collapse `.product-layout`, `.preview-layout`, and `.result-layout` to one column; keep all existing controls full-width where already specified. Let copy wrap naturally, preserve 44–48px controls, avoid sticky/fixed actions, and preserve the reduced-motion rules.

- [ ] **Step 5: Run both new layout regression tests**

Run: `$env:MODEL_PROVIDER='fake'; python -B -m unittest tests.test_web.WebDemoTests.test_editorial_regions_exist_across_all_three_stages tests.test_web.WebDemoTests.test_result_layout_uses_two_columns_on_desktop_and_one_on_mobile`

Expected: both tests pass, with two result columns at 768 px, one at 320/375/414 px, and no horizontal overflow at any tested width.

## Task 4: Full verification and visual review

**Files:**
- Verify: `codebase/web/index.html`
- Verify: `codebase/web/styles.css`
- Verify: `tests/test_web.py`

- [ ] **Step 1: Run the full test suite**

Run: `$env:MODEL_PROVIDER='fake'; python -B -m unittest discover -s tests`

Expected: 43 or more tests pass, with only an environment-dependent optional browser class skipped if its dependency/browser is unavailable. Investigate any new failure; do not change benchmarks or fixtures to make tests pass.

- [ ] **Step 2: Run repository and syntax checks**

Run: `python -B run.py check`

Expected: 24 benchmark cases valid and project checks pass.

Run: `node --check codebase/web/app.js; git diff --check`

Expected: both exit successfully.

- [ ] **Step 3: Browser-smoke the three real stages**

Use the local fake-model app and verify:

1. Product input still accepts the demo URL and both exact-variant selectors.
2. Preview shows the selected product, fixture/source warning, counts, and the same first five actual review records; expansion reveals the rest.
3. Analysis keeps the preview visible while pending, then renders the current mock/model label, verdict, coverage, citations, and advice.
4. “Đổi mẫu ốp”, back, retry, and keyboard focus behavior still work.
5. At 320, 375, 414, and 768 px, each state has no horizontal overflow and all actions remain reachable.

- [ ] **Step 4: Inspect final scope**

Run: `git status --short; git diff --stat; git diff --check`

Expected: changes are limited to the listed web/test files plus this plan; no backend, model, benchmark, cost, trace, or fixture artifacts changed.

## Plan self-review

- Spec coverage: all three stages, exact local data, source honesty, result hierarchy, responsive behavior, accessibility, and unchanged API/model/benchmark/cost boundaries are covered.
- Placeholders: no TODO/TBD or undefined implementation hooks; snippets use the current DOM IDs and existing token names.
- Test approach: structural behavior tests are written before layout implementation; visual composition is checked in a real browser at the agreed mobile widths.
