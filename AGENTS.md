# Codex Instructions — Onshape CAD Automation

Goal: Implement reliable, auditable, geometrically correct Onshape assembly editing based on user's explicit directions and engineering drawings.

1. Never expose, print, store, or commit credentials. Credentials must come from environment variables. If a credential appears in chat, instruct key rotation.
2. First inspect actual document/workspace/element information and confirm the element type; do not assume the element is an Assembly.
3. Before writing, inspect part instances, assembly hierarchy, existing mates, and mate connector definitions. Do not invent IDs or connector coordinate systems.
4. Default to read-only/dry-run. Before an API write, show intended operations, affected instances, mate type, connector selections, and expected degrees of freedom. Request approval for consequential changes.
5. Preserve existing design intent. Prefer precise CAD geometry and source drawing dimensions over image-derived approximations. Flag conflicting/underdimensioned requirements.
6. Create a named Onshape version or other safe rollback point before modifications. Check API errors and validate returned states after each modification.
7. Confirm final mates by querying the assembly again; log what actually changed versus what failed. Do not claim completion without verification.
8. Add focused tests, clear error messages, API timeouts, and controlled retry policies. Do not retry mutation requests blindly.
9. Keep all API endpoint details consistent with current official Onshape API documentation; verify before implementing any editing endpoint.

Initial milestone: read-only inspection, then a proposed mate plan. Do not call a write endpoint until the user has specified what should be mated.

The engineering drawing is authoritative. Inspect and render every page/view. Never invent dimensions or silently replace tolerances with nominal values. Every datum must retain provenance and be classified as `EXPLICIT`, `DERIVED`, `STANDARD-DEFINED`, `ASSUMED`, `UNRESOLVED`, or `ESTIMATED-NONAUTHORITATIVE`. Consequential uncertainty affecting geometry, fit, function, safety, compliance, or manufacturing blocks execution pending clarification.

Never mutate Onshape without approval of the exact target and exact plan. Exercise writes on a disposable document first, stop on regeneration error, and independently measure the result. Report `PASS`, `FAIL`, and `NOT_VERIFIED` honestly; use `VERIFIED` only when all critical checks pass and no consequential assumptions remain.

After software changes, run `python3 -m unittest discover -v`. Keep per-job evidence under `jobs/<job-id>/`. Do not commit drawing sources, page renders, logs, CAD exports, API response dumps, or secrets.
