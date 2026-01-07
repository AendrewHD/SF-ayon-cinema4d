## 2024-03-24 - Tooltips for Frame Ranges
**Learning:** In VFX pipelines, users often confuse "shot range" (cut length) with "work range" (includes handles). Adding explicit tooltips like "(without handles)" to standard attribute definitions prevents costly render errors.
**Action:** Always verify if `frameStart`/`frameEnd` inputs in creators/loaders need clarification about whether they include handles.
