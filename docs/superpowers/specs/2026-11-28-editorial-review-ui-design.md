# BacTrung editorial review UI — design

## Goal

Make the existing three-stage BacTrung flow feel like a considered review-reading
experience rather than a plain form followed by uniform text blocks. Keep the
warm-paper and deep-teal palette already approved. Add hierarchy through
composition, editorial typography, grouping, and useful context—not decorative
charts, invented product imagery, or extra product capabilities.

## Audience and decision

The audience is a shopper checking whether a specific phone-case variant is
worth considering. The interface should help them:

1. identify the exact product/model/variant being assessed;
2. inspect the actual local reviews that will be analyzed;
3. understand the recommendation and verify it against cited review evidence.

The user remains the decision-maker; the UI does not imply that BacTrung buys,
verifies media, or independently validates seller claims.

## Approved visual direction

Use the “Tạp chí review” / editorial-review direction shown in the approved
three-stage mockup. Preserve the current palette and three-stage information
architecture, but give each stage a stronger and more distinct composition:

- **Product selection:** a focused selection form with the chosen URL, model,
  and variant grouped as one product context. Keep the local-data/no-live-crawl
  explanation close to the link field and make the next action visually clear.
- **Review preview:** present the selected variant and source as a compact
  editorial heading/context block, followed by the actual review sample as
  readable, differentiated entries. Keep the true count and match count
  prominent, retain the expand/collapse behavior, and keep the analysis action
  visible without making the review list feel secondary.
- **Analysis result:** establish a clear reading order: text-labelled verdict,
  analyzed/matched count and source caveat, cited evidence, then buyer advice
  and expandable technical detail. Evidence entries should have visible
  distinctions between their role/label, review ID/rating, quotation, and
  explanation.

This is one coherent layout across the three states, not three unrelated
themes. On narrow screens it becomes a readable single-column document; on
larger screens, contextual notes and evidence may use a restrained secondary
column where it improves scanning.

## Research basis

- Baymard Institute’s review research says users use ratings distribution to
  orient themselves before reading selected reviews, and that review counts
  help readers interpret whether ratings are based on a meaningful sample.
  For BacTrung, this supports giving counts/source context visual prominence.
  It does **not** justify inventing an aggregate rating or distribution that the
  local response does not provide.
- Nielsen Norman Group’s progressive-disclosure guidance supports keeping the
  primary decision information visible first and placing secondary/technical
  detail behind a clear disclosure. The existing “Chi tiết phân tích” remains
  available but visually subordinate.
- WCAG 2.2 AA target-size minimum is 24×24 CSS px subject to its exceptions;
  this app already uses larger primary controls. Keep visible focus, native
  controls, semantic headings, and useful mobile tap targets.
- UI UX Pro Max’s UX guidance emphasizes hierarchy, contextual state feedback,
  honest loading, responsive reflow, and keeping complete text accessible.
  These are quality checks, not a reason to add motion or visual effects.

## Data honesty and boundaries

- Keep the approved warm-paper/deep-teal palette.
- Use only product context, counts, source labels, reviews, and analysis fields
  already returned by the local app. Do not create scores, star distributions,
  testimonials, summaries, review media thumbnails, or seller/product images.
- Preserve clear distinctions between collector-export data and synthetic
  local fixture data. Never imply a live Shopee crawl or fabricated progress.
- Keep the review preview visible while the existing analysis request is
  pending. Do not claim incremental processing if the API does not report it.
- Keep `/preview` and `/analyze` request/response contracts and model behavior
  unchanged.
- Do not modify `codebase/agent.py`, benchmark/evaluation inputs or results,
  cost simulation, trace outputs, or files owned by Quang or Minh.

## Accessibility and responsive behavior

- Maintain semantic page/section headings, labeled fields, step state,
  accessible status announcements, keyboard operation, and visible focus.
- Keep text-labelled recommendation states; color is supplementary only.
- Preserve full review text, wrapping, and the visible review expansion control.
- Preserve the existing reduced-motion behavior; avoid decorative/continuous
  animation.
- Verify the app at 320, 375, 414, and 768 CSS px with no horizontal overflow.

## Implementation scope

Expected files:

- `codebase/web/index.html` — editorial grouping/hierarchy for the three
  existing states.
- `codebase/web/styles.css` — layout, type hierarchy, review/evidence rhythm,
  contextual panels, and responsive rules using existing palette tokens.
- `codebase/web/app.js` — only if needed to expose existing state/context
  accessibly; no change to network or analysis behavior.
- `tests/test_web.py` — assert the staged content, review text/context,
  navigation and responsive behavior remain intact.

No backend, model, API contract, benchmark, evaluation, cost, or trace changes
are part of this design.

## Validation

- Run the full unittest suite with `MODEL_PROVIDER=fake`.
- Run `python -B run.py check`.
- Run `node --check codebase/web/app.js` and `git diff --check`.
- Browser-smoke all three actual states, including the fixture source label,
  exact-variant review content, result evidence, and change-product action.
- Check 320/375/414/768 px viewports for overflow and readable controls.

## Source links

- Baymard, ratings distribution summary:
  https://baymard.com/research-articles/user-ratings-distribution-summary
- Baymard, showing number of ratings:
  https://baymard.com/research-articles/user-perception-of-product-ratings
- Nielsen Norman Group, progressive disclosure:
  https://www.nngroup.com/articles/progressive-disclosure/
- W3C, WCAG 2.2 target size minimum:
  https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- UI UX Pro Max, UX guidelines:
  https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/src/ui-ux-pro-max/data/ux-guidelines.csv
