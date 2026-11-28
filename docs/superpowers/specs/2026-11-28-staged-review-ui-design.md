# Staged review-analysis UI — design

## Goal

Help an end user quickly inspect the reviews relevant to the selected phone
model and case variant, then understand the AI recommendation and its evidence.
The interface should feel more informative than the current single-screen form
without adding noisy motion or implying work that did not happen.

## User flow

1. **Choose product:** enter or choose a supported product URL, then choose the
   exact phone model and case variant.
2. **Review preview:** retrieve the matching review set from the app's current
   local dataset and show its actual review count, match count, and a compact
   sample of the review text/media. The user can expand the list and proceed to
   analysis.
3. **AI analysis and result:** while the existing analysis request is pending,
   keep the preview visible and show a calm, factual status. When the response
   arrives, transition to the existing result content: recommendation,
   coverage, evidence, advice, and expandable details.

Each stage has a clear heading and step indicator. Preserve the selected
product context between stages and provide a way to go back and change it.
Errors stay in the relevant stage, explain what happened, and offer a safe
retry or correction without presenting a recommendation.

## Data and honesty constraints

- The CP4 demo must not start a live Shopee crawl. This is an explicit project
  constraint; current app behavior uses local fixture data or an already
  available collector export.
- The preview must contain real records returned by the local app, filtered
  using the same product URL, exact phone model, and exact case variant as the
  analysis flow. Do not synthesize review cards or staged crawl events.
- The app currently returns analysis as one synchronous response. The UI may
  show a pending state while that request is actually running, but must not
  claim that individual reviews are being fetched incrementally unless the
  backend actually supplies such events.
- Clearly label the active data source (synthetic local fixture versus
  collector export); do not imply local data was fetched live.
- Keep the analysis contract and scoring behavior unchanged. Do not edit
  `codebase/agent.py`, benchmark cases/criteria, run-1 artifacts, or cost
  simulation.

## Interaction and presentation

- Use a low-noise progress treatment: numbered stages, one persistent status
  line, and restrained transitions. Respect reduced-motion preferences.
- In preview, show a small number of readable review rows/cards first, with a
  clearly labelled expand/collapse control for the rest. Show rating, review
  ID, text, and available-media indication without relying on color alone.
  The current server does not serve review media as browser assets, so this
  iteration will not embed media thumbnails.
- Do not auto-scroll while the user is reading. Keep controls usable on mobile
  and maintain keyboard focus, labels, live status announcements, and existing
  error behavior.
- The analysis action is explicit so the user can inspect the exact local
  sample before asking the model to evaluate it.

## Implementation boundary

Expected changes are limited to the UI-owned server/API and web presentation:

- `codebase/app.py`: add a read-only `POST /preview` endpoint calling the
  existing `get_product_reviews` lookup and deterministic sampling helper
  with the same request values/seed as the analysis flow; return only fields
  needed by the preview.
- `codebase/web/index.html`: add stage structure, review preview region, and
  navigation/status controls.
- `codebase/web/app.js`: manage stage transitions, preview loading, analysis
  pending state, retry/back behavior, and safe DOM rendering.
- `codebase/web/styles.css`: style the staged flow and responsive review list.
- `tests/test_web.py` and, if needed, `tests/test_app.py`: cover exact-match
  preview behavior, state transitions, errors, keyboard access, and mobile
  overflow.

No files owned by Minh or Quang are in scope. The existing analysis endpoint
and its request/response contract remain unchanged.

## Validation

- Unit/integration tests prove preview excludes other products, models, and
  variants and does not expose unrelated dataset fields.
- Browser tests cover all stages, no-data/error states, retry/back, and
  preserved result behavior.
- Responsive and keyboard checks run at the project's existing target sizes.
- Visual smoke verifies that review preview remains visible during the actual
  model request and that no false crawl-progress claim is shown.

## Technical confirmation

The existing `get_product_reviews` helper already performs exact URL, model,
and variant matching, deterministic star-group sampling, and returns review
IDs/text/media metadata plus source labels. The preview endpoint can reuse it
directly and project a minimal safe response, avoiding a second selection
implementation. The existing `/analyze` contract remains unchanged.
