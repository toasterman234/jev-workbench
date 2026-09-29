# Jev Workbench — Phase 1D evaluation report

Date: 2026-09-28 (run) / 2026-09-29 (analysis). Model: jev-1.13.0 (TypeSafe, real provider, no stubbing).
Config branch: `work/work-judgment-instructions-v1d` @ `3ab0e96c752659fe0a99f261bbb7fb98fae770fc` — instruction rewrites only; vocabularies, enums, review rules, schemas, provider, model unchanged.
Suite: `eval-run/suite-phase1c-v2.yaml` (reused unchanged, wj-011 re-gold carried). Eval branch: `work/eval-phase1d-2026-09-28` (not merged, no PR comment).

## Method

- Fresh isolated instance on port 17424 with its own JEV_HOME; production untouched. Node 24.
- Six judgment functions created from the canonical v1d JSONs **verbatim** (sha256-verified; only the provenance `changelog` top-level field stripped because the workbench schema rejects it — HTTP 422; review rules byte-identical and live — review reasons fired on 83 scored records).
- Both modes on the full 30-case suite: component (Mode A, gold inputs) and end-to-end (Mode B, chained predictions).
- `TYPESAFE_API_KEY` read from environment only; workbench issued a fresh API client whose token was held in memory and never written to disk.
- 342 invocations attempted; 1 provider 502 (B/wj-004/select_artifact, retried 3x then excluded), 1 skipped_upstream_error; 324 scored.
- Driver bugs found and fixed mid-run (cookie passed positionally on a GET helper; DELETE missing the CSRF header during idempotent cleanup); both were harness-only and did not affect scored predictions.

## Scores vs Phase 1C (v2)

| judgment | 1C component | 1D component | 1C end-to-end | 1D end-to-end |
|---|---|---|---|---|
| classify_data_type | 17/29=58.6% | 16/30=53.3% | 18/30=60.0% | 16/30=53.3% |
| next_intent | 23/30=76.7% | 25/30=83.3% | 22/29=75.9% | 23/30=76.7% |
| select_artifact | 23/28=82.1% | 25/28=89.3% | 19/27=70.4% | 20/27=74.1% |
| select_playbook | 21/27=77.8% | 22/27=81.5% | 17/26=65.4% | 17/26=65.4% |
| requires_human_gate | 27/29=93.1% | 29/29=100.0% | 26/28=92.9% | 29/29=100.0% |
| evidence_satisfies_exit | 18/19=94.7% | 19/19=100.0% | 18/19=94.7% | 18/19=94.7% |
| **total** | **129/162=79.6%** | **136/163=83.4%** | **120/159=75.5%** | **123/161=76.4%** |

- **Component: 79.6% → 83.4% (+3.8pp). End-to-end: 75.5% → 76.4% (+0.9pp).**
- Biggest wins: `requires_human_gate` reached 100% in both modes (93% → 100%), `select_artifact` +7.2pp component / +3.7pp E2E, `next_intent` +6.6pp component.
- One real regression: `classify_data_type` fell to 53.3% in both modes (was 58.6% / 60.0%) — now the clear bottleneck.

## Noul judgments (no thresholds changed)

| judgment | mode | Brier | acc@0.50 | acc@provisional |
|---|---|---|---|---|
| requires_human_gate | A | 0.036 | 100.0% | 100.0% @ 0.70 |
| evidence_satisfies_exit | A | 0.035 | 100.0% | 78.9% @ 0.80 |
| requires_human_gate | B | 0.043 | 100.0% | 100.0% @ 0.70 |
| evidence_satisfies_exit | B | 0.039 | 94.7% | 84.2% @ 0.80 |

- Gate Brier improved 0.061/0.070 → 0.036/0.043; exit Brier 0.037/0.033 → 0.035/0.039. Provisional thresholds not yet met for exit@0.80 (78.9%/84.2%).

## Resolution analysis

- Of the 45 Phase-1B instruction-attributed mismatch cells: **24 resolved in 1D, 20 still wrong, 1 not scored** (the B/wj-004 select_artifact provider 502).
- On the 319 cells scored in both 1C and 1D: **19 resolved, 17 regressed** (net +2; the headline gains come mostly from cells 1C could not score plus the resolved set).

### Patterns that worked (19 resolved)
- **request discriminators**: wj-001 (review_request→request), wj-004 (open_question→request), wj-005/wj-021 (unclear/open_question→request) — the 'an ask for work/attention/approval/evaluation is a request' line fired.
- **verify → verification_evidence**: wj-002, wj-008, wj-009, wj-003(B).
- **decide → decision**: wj-019 select_artifact (result→decision).
- **research vs verify**: wj-003 next_intent (research→verify).
- **intent-fit playbooks**: wj-004 (none_required→technical_project_exploration), wj-019 (root_cause_analysis→decision_assessment).
- **close-loop**: wj-029 next_intent (execute→close). **execute-on-plan**: wj-028 select_artifact (result→plan).

### Regressions — the rewrite overshot (17)
- **unclear_needs_review suppression backfired on wj-025** (both modes): gold is `unclear_needs_review`, the new 'vagueness alone is not unclear' line pushed the model to request/clarify. **This is a direct instruction↔gold conflict — flagged for Ben, not auto-fixed.**
- **'sign-off is verification' overshoot**: wj-030 classify (decision→verification) and wj-023/wj-030 select_artifact (result→verification_evidence) in Mode B.
- **'update the approved plan' overshoot**: wj-010 select_artifact (result→plan, Mode A).
- **'fit the playbook to the intent' overshoot**: wj-006 select_playbook (none_required→decision_assessment, Mode A).
- **note/container lines wobble**: wj-006 classify (request→note), wj-028 classify (plan→state_note), wj-005/wj-006 select_artifact (none_required→unclear_needs_review).
- **wj-007 classify (plan→quality_failure)** is an unexplained destabilization worth watching.

## Fresh mismatch attributions (65 Phase-1D mismatches)

- judgment instructions: 31; bad expected label: 14; upstream error: 19; insufficient context: 1
- 16 cells flagged `gold_review_needed` (incl. wj-008/wj-013/wj-015 per Ben's standing call, plus the new wj-025 instruction/gold conflict).
- E2E cascade: 19 of 65 mismatches are upstream-driven (mode B inherits wrong object_type/intent), vs 19 in 1B — the cascade is unchanged in size.

## Top remaining pattern

`classify_data_type` is now the binding constraint: 53.3% in both modes, 28 of 65 mismatches, and the only judgment that moved backwards. The discriminators that fixed request/verify/decide boundaries are too strong — they overshoot into note/state_note/verification where the gold wants the container or the original act. The next iteration should add **negative guards** ('an approval record is still a decision, not verification'; 'a plan being updated is still a plan, not a state_note') rather than more positive discriminators. wj-025 also needs a ruling before the unclear line is touched again.

## Open items (Ben's calls — not re-golded)

- wj-008, wj-013, wj-015 golds remain Ben's calls (unchanged from Phase 1C).
- NEW: wj-025 classify/next_intent — 1D instruction contradicts gold unclear_needs_review; needs adjudication before any further instruction edit.
- Provisional thresholds (gate 0.70, exit 0.80) reported only; no calibration performed.
- PR #2 remains unmerged; nothing posted to it in Phase 1D.

## Artifacts

- `eval-run/results-phase1d-2026-09-28.json`, `eval-run/mismatches-phase1d-2026-09-28.json`, `eval-run/attributions-phase1d.json`, `eval-run/run_phase1d.py`, `eval-run/manifest-phase1d.json` (to be written at commit).
- Canonical v1d configs on `work/work-judgment-instructions-v1d` @ `3ab0e96c`; posted drafts sha256-verified against them (minus the stripped provenance `changelog`).

