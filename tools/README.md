# DD carousel render toolkit

Turns a carousel spec (JSON) into 1080×1350 PNG slides in the Digitally Defamed visual system. The layout is ported from the original 43-carousel bank.

## Render

```bash
pip install playwright && python3 -m playwright install chromium   # once
python3 tools/render.py tools/carousels/bank-02.json --out out/bank-02
```

The last line printed is `OK` when every slide rendered and passed the checks. Anything else (`FAILED`, `TEST-ONLY`) means the PNGs must not be published. After `OK`, open a few slides and check them by eye.

Output: `slide-01.png` … `slide-NN.png` in the `--out` folder.

## Spec format

```json
{
  "id": "bank-02",
  "tab": "Google · 02",
  "counter": false,
  "slides": [
    {"type": "hook",  "headline": "…"},
    {"type": "point", "headline": "…", "body": "…"},
    {"type": "cta",   "headline": "Send us the link. We'll tell you if it may have a case.",
                      "button": "DM the word REVIEW", "sub": "You only pay once it's gone."}
  ]
}
```

- `hook`: first slide. Large headline, red rule, "Swipe →".
- `point`: headline, red rule and optional body (a string, or a list of paragraphs), centered vertically.
- `cta`: last slide. Dark background, red mark, headline, red button, sub-line. For a "Save this" or "Follow" ending, put that in `headline`/`button`.
- `tab`: top-left label, shown uppercase, e.g. "Google · 02", "Reddit · 07".
- `counter`: optional `true` adds "3/8" bottom-right on point and CTA slides. Off by default, matching the bank.
- 6–9 slides; new carousels should have 7–9.

## Checks (render fails on these)

- First slide is `hook`, last is `cta`.
- Text stays inside the 96px side margins and clear of the tab and footer.
- Point slides aren't overfilled.
- Hard content rules: no "guaranteed", "we delete", "any review", "permanent", warranties, percentages, unfilled `[placeholders]` (brackets inside “quotes”, like “[your brand] reviews”, are allowed), plus any terms in the `DD_BANNED_TERMS` environment variable (comma-separated; kept out of this public repo).
- Non-US spellings (enquiry, maths, defence…) print a `WARN`; fix them before publishing.

These catch mechanical problems only. Every slide still has to be read against the content rules in the DD content spec.

## Design tokens

| Token | Value |
|---|---|
| Paper | `#F3F0E8` |
| Ink | `#15171A` |
| Body text | `#2E3136` |
| Tab text | `#55585E` |
| Red accent | `#FF3F44` |
| Dark-slide sub text | `#CFCAC0` |
| Headlines | Fraunces SemiBold (wght 600, opsz 36) |
| Everything else | Inter (Regular 400, Medium 500, SemiBold 600) |

## Files

- `template.html`: the single slide template (CSS + builder).
- `render.py`: renders a spec with Playwright and runs the checks.
- `assets/`: wordmark (ink and paper versions) and the red mark, extracted from the original bank.
- `fonts/`: font files, loaded locally so renders don't need the internet.
  - Inter: included.
  - Fraunces: `Fraunces-Variable.ttf`, used at weight 600, optical size 36. If it's missing the render stops with an error.
- `carousels/`: carousel specs.

Both fonts are licensed under the SIL Open Font License; see `fonts/LICENSE-*.txt`.
