# Jev Workbench — Judgment Evaluation, Phase 1B (2026-09-28)

Branch: `work/eval-phase1b-2026-09-28` · Model: `jev-1.13.0` · Suite: `phase1b-v1` (30 cases)
Modes: **A component** (gold upstream labels) and **B end-to-end** (predicted labels fed forward)

## Headline

| Mode | Scored | Accuracy |
|---|---|---|
| A — component (gold upstream) | 125/161 | **77.6%** |
| B — end-to-end (predicted upstream) | 114/158 | **72.2%** |

On the 25 carried baseline cases, Mode A scored **105/134 = 78.4%** vs the Phase 1 baseline of 93/135 = 68.9% (**+9.5pp**). The `incident` vocabulary amendment classified 4/4 scored incident cases correctly in both modes (the 5th errored on a provider contract violation, both modes).

Phase 1 baseline (`work/eval-phase1-2026-09-28`, `eval-report-2026-09-28.md`, `eval-run/results-2026-09-28.json`) is preserved untouched.

## Mandate compliance

- Six configs taken from `origin/work/work-judgment-phase1` (`2fcac3effc610060383722f0967023a54a364b36`), never regenerated from `plans/judgment-contracts.yaml`. SHA-256 recorded below.
- Review rules preserved byte-identical, including the Phase 1B `incident` amendment (verified: amended classifier's `review` block == canonical `review` block).
- `TYPESAFE_API_KEY` read from process environment only, presence-checked fail-closed; the value was never printed, logged, or persisted, and no client token was written to disk (client tokens lived in process memory only).
- Classification treated as semantic object type; source/container type passed separately (`source_type`, never as the classification input).
- `incident` activated as a Phase 1B vocabulary candidate with provenance (see §4).
- Structured context supported for `next_intent` (current_state, known_artifacts/decisions, blockers_or_unknowns, implementation_complete, browser_or_ui_in_scope, current_lifecycle); nothing invented — fields passed only when the case supplied them.
- Thresholds reported at 0.50/0.70 (gate) and 0.50/0.80 (exit) with raw probabilities and Brier scores; **no threshold calibration** performed on this sample.
- Five synthetic positive `evidence_satisfies_exit=true` cases, explicitly marked `synthetic: true` with provenance.
- No predictions fabricated: every scored invoke is a real `jev-1.13.0` response (319 scored; 3 provider-contract errors recorded as errors, not scores).
- Prior results never overwritten; baseline gold labels never modified.

## 1. Setup & provenance

Isolated workbench: `JEV_HOME=/Users/bencharney/.jev-workbench-phase1b-eval`, port 17422, Node v24.16.0. Production `~/.jev-workbench`/port 17420 untouched.

Provider check (fail-closed): `/api/admin/status` → `{"configured": true, "source": "environment", "masked": "•••••6cd6"}`. The run refuses to proceed unless `source == "environment"`.

### Config checksums (canonical, from `origin/work/work-judgment-phase1`)

| Function | SHA-256 |
|---|---|
| classify_data_type | `08f49b5443b5d36effff4c01ed941da7a4de7ffc4b8096575fb298a2dbcd4e83` |
| next_intent | `36179a85bf8ad96ab0c29d8d060c6174fd8da8986aa939ff49f6e222a5d6c90d` |
| select_artifact | `d8a320f8841429184892cad334870c74e728a8d73383342f0df71e0c145a1d05` |
| select_playbook | `ec4fb5306ff502b86e3cdd44089af6ead6b11f47906267a7fc8d3b28604c4165` |
| requires_human_gate | `eb49d3d8ec6f9f6fd2a6c625830d4b29778ad379c428a30ef38447ef77efe0e6` |
| evidence_satisfies_exit | `7f9b844195fee52220200837fc2e741e24a322d0ec5df366877288b5ff29e364` |

All six pin `provider: typesafe`, `model: jev-1.13.0`. All six were smoke-previewed (6/6 ok) and published+activated as version 1.

### Incident amendment (Phase 1B vocabulary candidate)

The canonical `classify_data_type.json` has no `incident` choice, but the mandate requires `incident` as an active Phase 1B candidate while using the exact configs. Resolution, done transparently:

- The six canonical files were used byte-identical as source (checksums above).
- A versioned Phase 1B **effective classifier** was derived by the single minimal change: adding `incident` to `questions.primary_data_type.criteria` ("An operational incident: an unplanned disruption, failure, outage, or urgent problem requiring diagnosis, response, and prevention.") and to the output enum (inserted before `other_needs_new`).
- Review rules verified byte-identical to canonical.
- Effective classifier SHA-256 (sort_keys JSON): `66891919c1c80ff477d4df45fa35282d34ef073f6a7dc21851ad51310a8fdf46`.
- The live workbench draft was re-verified by checksum at rerun time (`verified_draft_sha256` in `manifest-phase1b.json`).

It is **not** claimed byte-identical to the canonical file; both checksums are recorded.

### Run incident (provenance note)

The first setup run created all six functions, passed all six smoke previews, created the API client, and completed 79 real invocations before the workbench host process was killed (stale lock recovered via `service recover`; one leftover `running` row marked interrupted). The rerun reused the existing functions after verifying each live draft's checksum against the intended configs (fail-closed on mismatch), created a fresh client, and completed all 339 invocations with per-record checkpointing. The 79 orphan invocations remain in the isolated DB only; scoring uses the completed run's records.

## 2. Suite composition (`eval-run/suite-phase1b-v1.yaml`)

- 30 cases: **25 carried** from the Phase 1 suite (labels unchanged; baseline golds preserved) + **5 new synthetic** positive-exit cases (`wj-026`..`wj-030`, `synthetic: true`).
- 5 carried cases (`wj-011`..`wj-015`) change expected classification from `other_needs_new` to `incident`, each carrying `delta_vs_baseline` with provenance citing its pre-existing `vocabulary_candidate: incident`.
- Expected-label counts: classify 30, next_intent 30, select_artifact 27, select_playbook 27, requires_human_gate 29, evidence_satisfies_exit 19 (12 false / 7 true — the 5 synthetic cases balance the 12/2 baseline skew).
- Suite generator preserved: `eval-run/generate_suite_phase1b.py`.

## 3. Method

- **Mode A (component):** each judgment invoked with gold upstream labels (teacher forcing). `next_intent` additionally receives gold `object_type`; `select_artifact`/`select_playbook` receive gold `next_intent` (+ gold artifact/object type where the contract supports them).
- **Mode B (end-to-end):** fixed chain classify → next_intent → select_artifact → select_playbook → requires_human_gate → evidence_satisfies_exit; each step feeds the *predicted* upstream values. All six judgments invoked per case; only judgments with gold labels are scored. If an upstream invoke errors, the dependent invoke is skipped (counted separately, not scored).
- Choice judgments scored by exact match. Noul judgments scored by Brier score plus accuracy at 0.50 and at the provisional exit thresholds (0.70 gate / 0.80 exit).
- Review rules active throughout; `review_reasons` recorded per invoke and aggregated by rule id.

## 4. Results

### Per judgment per mode

**Mode A — component**

| Judgment | Correct | Accuracy | Brier | acc@0.50 | acc@provisional | Review triggers |
|---|---|---|---|---|---|---|
| classify_data_type | 16/29 | 55.2% | — | — | — | low_confidence 17, unclear 2 |
| next_intent | 22/30 | 73.3% | — | — | — | low_confidence 12, unclear 1 |
| select_artifact | 20/27 | 74.1% | — | — | — | low_confidence 13 |
| select_playbook | 21/27 | 77.8% | — | — | — | low_confidence 7, new_playbook_needed 1 |
| requires_human_gate | 27/29 | 93.1% | 0.061 | 93.1% | 100% @0.70 | ambiguous_gate 3 |
| evidence_satisfies_exit | 19/19 | 100% | 0.037 | 100% | 78.9% @0.80 | ambiguous_exit 3 |

**Mode B — end-to-end**

| Judgment | Correct | Accuracy | Brier | acc@0.50 | acc@provisional | Review triggers |
|---|---|---|---|---|---|---|
| classify_data_type | 17/29 | 58.6% | — | — | — | low_confidence 17, unclear 2 |
| next_intent | 21/29 | 72.4% | — | — | — | low_confidence 13, unclear 1 |
| select_artifact | 15/27 | 55.6% | — | — | — | low_confidence 13, unclear 1, new_vocab_needed 1 |
| select_playbook | 17/26 | 65.4% | — | — | — | low_confidence 3, unclear 1, new_playbook_needed 1 |
| requires_human_gate | 25/28 | 89.3% | 0.070 | 89.3% | 100% @0.70 | ambiguous_gate 4 |
| evidence_satisfies_exit | 19/19 | 100% | 0.033 | 100% | 78.9% @0.80 | ambiguous_exit 4 |

### Baseline comparison (25 carried cases, Mode A)

| Judgment | Phase 1 baseline | Phase 1B carried | Δ |
|---|---|---|---|
| classify_data_type | 37.5% | 54.2% (13/24) | +16.7pp |
| next_intent | 56.0% | 76.0% (19/25) | +20.0pp |
| select_artifact | 75.0% | 82.6% (19/23) | +7.6pp |
| select_playbook | 83.3% | 75.0% (18/24) | −8.3pp |
| requires_human_gate | 79.2% | 91.7% (22/24) | +12.5pp |
| evidence_satisfies_exit | 92.9% | 100% (14/14) | +7.1pp |
| **overall** | **68.9% (93/135)** | **78.4% (105/134)** | **+9.5pp** |

Caveat: "same cases" but not "same inputs" — Phase 1B passes structured context (current_state, blockers, known artifacts/decisions) and gold `object_type` into `next_intent`, and the classifier carries the `incident` amendment. The next_intent jump (+20pp) is plausibly the structured context; the select_playbook dip (−8.3pp) traces to the wj-012/wj-013 gold inconsistencies (§7).

Synthetic cases (wj-026..030), Mode A: 20/27 = 74.1%.

### Thresholds (reported, not tuned)

- requires_human_gate: the provisional 0.70 threshold classifies all scored cases correctly in both modes (100%), vs 93.1%/89.3% at 0.50. The misses at 0.50 are p≈0.55–0.57 hedges on minimal gate context. **Not a calibration recommendation** — n=29/28 is far too small; reported for the record.
- evidence_satisfies_exit: 100% at 0.50, 78.9% at the provisional 0.80 exit threshold, Brier 0.037/0.033 (well-calibrated probabilities on this sample).

### Review-trigger summary

`low_confidence` dominates (choice judgments): 17+12+13+7 in A, 17+13+13+3 in B. `unclear` fired 3+3 times on genuinely vague inputs. `ambiguous_gate`/`ambiguous_exit` fired on the noul review bands (3+3 A, 4+4 B) — the bands are doing their job on hedged probabilities. `new_playbook_needed` fired twice (wj-024, the behavior-regression gap case — correct signal). `new_vocab_needed` fired once (B-wj-024 artifact → `other_needs_new`, also a correct signal: the case is about a missing playbook).

## 5. Confusion tables (Mode A)

**classify_data_type** (29 scored): `request` golds scatter across 6 predictions (only 2/8 correct) — the weakest category. `github_issue` 5/5, `incident` 4/4 (+1 error), `plan` 2/2, `decision` 1/2, `result` 0/1, `evidence` 0/1, `verification` 0/1, `work_item` 1/4, `unclear_needs_review` 1/1.

| gold \ pred | request | review_request | evidence | incident | open_question | unclear | risk | plan | verification | note | state_note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| request (8) | 2 | 1 | 1 | 1 | 1 | 1 | 1 | — | — | — | — |
| work_item (4) | — | — | — | 1 | — | — | — | 1 | 1 | — | 1* |
| decision (2) | — | — | — | — | 1 | — | — | — | — | — | — |
| evidence (1) | — | — | — | — | — | — | — | — | — | 1 | — |
| verification (1) | — | — | — | — | — | — | — | — | — | — | 1 |
| result (1) | — | 1† | — | — | — | — | — | — | — | — | — |

\* work_item→work_item 1 correct. † result→evidence.
(`github_issue` 5/5, `incident` 4/4, `plan` 2/2, `unclear_needs_review` 1/1 correct — omitted for brevity.)

**next_intent** (30 scored): errors scatter; no single systematic confusion. verify→research (1), close→review/execute (2), clarify→decide (1), decide→clarify (1), review→decide (1), plan→clarify (1), execute→plan (1).

**select_artifact** (27 scored): systematic pattern — **gold `result` → predicted `work_item_change`, 4/4** (wj-020, wj-023, wj-026, wj-029). All four are `close`-intent closeouts. Also verification_evidence→work_item_change (1), plan→run_record (1).

**select_playbook** (27 scored): gold `root_cause_analysis` → research_and_synthesis (2; the inconsistent wj-012/013 golds), → browser_ui_verification (1); technical_project_exploration → none_required (1); decision_assessment → root_cause_analysis (1); none_required → browser_ui_verification (1).

Mode B confusion tables are in `eval-run/mismatches-phase1b-2026-09-28.json` (every mismatch carries gold, predicted, p, review status/reasons, upstream values, and the upstream_error flag).

## 6. Error attribution (80 mismatches + 3 errors)

Each item attributed to exactly one bucket (`eval-run/attributions-phase1b.json`, with rationale per item):

| Bucket | Count | Share |
|---|---|---|
| judgment instructions (ambiguous criteria boundaries) | 45 | 54% |
| upstream error (wrong predicted label fed forward; Mode B only) | 19 | 23% |
| bad expected label (gold inconsistent or mismatched to the observation) | 8 | 10% |
| insufficient context (gate inputs with only next_intent; p≈0.55 hedges) | 4 | 5% |
| source-object-type ambiguity (object vs source/container conflation) | 4 | 5% |
| actual Workbench limitation (provider 502s, §8) | 3 | 4% |
| vocabulary gap | 0 | 0% |

Notes:

- **Judgment instructions dominate.** The recurring patterns: `result` vs `work_item_change` for close intent (4/4 in Mode A); `request` vs `open_question`/`review_request`/`risk`/`evidence` boundaries; `clarify`/`decide`/`review`/`plan` boundaries in next_intent; playbook precedence when `browser_or_ui_in_scope` is set. These are criteria-wording problems, not model failures per se — the model is choosing defensible answers at ambiguous boundaries (most fired `low_confidence`).
- **Upstream error (19, all Mode B)** is the cost of chaining: a wrong classify/next_intent prediction cascades. Mode B trails Mode A by 5.4pp overall (72.2% vs 77.6%); the gap concentrates in select_artifact (74.1%→55.6%) and select_playbook (77.8%→65.4%), the two judgments with the longest upstream chains.
- **Bad expected label (8 records = 4 case-judgments × 2 modes):** wj-003-classify (observation is a screenshot; gold `request`), wj-010-classify (observation is a plan; gold `work_item`), wj-012/wj-013-select_playbook (gold intent=research + gold artifact=research but gold playbook=root_cause_analysis — internally inconsistent; the model correctly matched the gold intent).
- **Vocabulary gap = 0** is itself a finding: the Phase 1 gap (`incident` → `other_needs_new`) is closed — 4/4 scored incident cases correct in both modes, and the one `new_vocab_needed` trigger (wj-024) fired correctly on a genuine coverage gap.
- No silent gold changes: all attributions reference the golds as-shipped in `suite-phase1b-v1.yaml`.

## 7. gold_review_needed

29 records flagged (16 case-judgments). Tier 1 — gold likely wrong (fix before reuse as ground truth): wj-003-classify, wj-010-classify, wj-012-select_playbook, wj-013-select_playbook. Tier 2 — gold debatable, model's answer defensible (human adjudication recommended): wj-001-classify (request/review_request), wj-002-classify and wj-009-classify (incident-amendment scope: does a botched deliverable count as an "incident"?), wj-006-next_intent (clarify/decide), wj-007-next_intent (review/decide), wj-008-select_playbook, wj-018-select_playbook, wj-021-classify, wj-022-classify, wj-024-next_intent, wj-027-classify, wj-029-classify. Full list with rationales in `attributions-phase1b.json`.

## 8. Errors (3)

All three are HTTP 502 `UPSTREAM_INVALID_RESPONSE` ("provider response did not conform to the question contract") — the TypeSafe provider returned a malformed response and the workbench faithfully surfaced it; no judgment was produced and none was scored:

- A-wj-014-classify_data_type, B-wj-014-classify_data_type (incident case — hence 4/4 scored, not 5/5)
- A-wj-016-select_artifact

Attributed to **actual Workbench limitation** (pipeline could not produce a judgment). Not retried beyond the script's single 5xx retry; not scored.

## 9. Invocation accounting

| | Count |
|---|---|
| Attempted invokes | 339 |
| Errored (502, recorded, unscored) | 3 |
| Scored | 319 |
| Attempted but unscored (Mode B judgments with no gold label) | 17 |
| Skipped (upstream invoke errored in Mode B chain) | 4 |
| Smoke previews (setup) | 6 attempted, 6 ok |

Mode A invoked 161 judgments; Mode B invoked 158 scored + 17 unscored + 4 skipped. No stale "untracked" language: every file produced is listed in §10.

## 10. Findings & limitations

1. **Component accuracy rose from 68.9% to 77.6%** (+9.5pp on carried cases), driven by structured context for next_intent (+20pp) and the incident amendment. End-to-end trails component by ~5pp due to upstream error cascade, concentrated in the two longest chains (artifact, playbook).
2. **The incident amendment works**: 4/4 scored incident cases correct in both modes, review rules untouched, no regression on other categories attributable to it. Open scope question: the amended criteria also fires on botched-deliverable cases (wj-002, wj-009) whose golds stayed request/work_item — needs a human call on whether "incident" should cover quality failures or only operational ones.
3. **Choice probabilities are well-behaved but hedged**: `low_confidence` is the dominant review trigger, and most mismatches fired it — the review queue would catch the majority of errors. Noul Brier scores (0.033–0.070) are good on this sample; thresholds reported but explicitly not calibrated here.
4. **Systematic criteria gaps to fix in contracts** (not code): result vs work_item_change for close intent; request-category boundaries (2/8 correct); playbook precedence with browser_or_ui_in_scope; clarify/decide/review boundaries.
5. **Limitations**: n=30 cases; synthetic positives are clearly marked but synthetic; 3 provider-contract errors; gold labels carry the Tier 1/2 issues above — do not treat current golds as settled ground truth without the §7 review.

## 11. Files (all on `work/eval-phase1b-2026-09-28`)

- `eval-report-phase1b-2026-09-28.md` — this report
- `eval-run/suite-phase1b-v1.yaml` — 30-case suite (25 carried + 5 synthetic)
- `eval-run/generate_suite_phase1b.py` — suite generator (provenance)
- `eval-run/run_phase1b.py` — setup + run + score driver (env-only key, fail-closed, checkpointed)
- `eval-run/results-phase1b-2026-09-28.json` — 339 records with inputs, predictions, review reasons, raw responses (no tokens)
- `eval-run/mismatches-phase1b-2026-09-28.json` — 80 mismatches with upstream_error flags
- `eval-run/attributions-phase1b.json` — 83 attributions with rationales + gold_review_needed flags
- `eval-run/manifest-phase1b.json` — config SHAs, function IDs/versions, verified draft SHAs, previews (no tokens)
- `eval-run/checkpoint-phase1b.jsonl` — per-record checkpoint (resume support)

Phase 1 artifacts (`eval-report-2026-09-28.md`, `eval-run/results-2026-09-28.json`, `eval-run/setup.py`, `eval-run/run.py`, `eval-run/setup-out.json`) unchanged.
