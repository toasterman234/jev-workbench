# Jev Workbench Phase 1 Evaluation Report

Date: 2026-09-28. Checkout: PR #2 HEAD `2fcac3effc610060383722f0967023a54a364b36` (detached, untouched).

## Method

- Isolated workbench instance on `127.0.0.1:17421` with fresh `JEV_HOME=/Users/bencharney/.jev-workbench-pr2-eval`; the production instance (`~/.jev-workbench`, port 17420) was not touched.
- Six judgment functions instantiated from PR #1 `plans/judgment-contracts.yaml`, published and activated as version 1, all with provider `typesafe` and pinned model `jev-1.13.0`.
- All 25 cases from PR #1 `plans/evaluation-cases.yaml`; each case ran ONLY the judgments in its `expected` map (sparse targets). 135 real TypeSafe invocations, 0 fabricated.
- Upstream conditioning (teacher forcing): `select_artifact` and `select_playbook` received the case's gold `next_intent` (required input); `select_playbook` also received gold `artifact_type` when present; `requires_human_gate` received gold `next_intent` as optional context. `classify_data_type` received the case `source.ref` as `source_ref`. Everything else came from the observation summary alone.
- Review rules were intentionally NOT instantiated: they would null the raw prediction for exactly the boundary labels this eval measures (other_needs_new / unclear_needs_review). Accuracy is scored on raw judgment output.
- Choice accuracy: predicted choice == gold label. Noul accuracy: boolean gold vs (probability >= 0.50); raw probabilities are recorded for later threshold calibration.

## Per-judgment accuracy

| Judgment | n | Correct | Accuracy |
|---|---|---|---|
| classify_data_type | 24 | 9 | 37.5% |
| next_intent | 25 | 14 | 56.0% |
| select_artifact | 24 | 18 | 75.0% |
| select_playbook | 24 | 20 | 83.3% |
| requires_human_gate | 24 | 19 | 79.2% |
| evidence_satisfies_exit | 14 | 13 | 92.9% |
| **Overall** | **135** | **93** | **68.9%** |

## Mismatches (gold labels NOT changed)

| Case | Judgment | Gold | Predicted |
|---|---|---|---|
| wj-001 | classify_data_type | `request` | `session` |
| wj-001 | next_intent | `execute` | `clarify` |
| wj-001 | requires_human_gate | `False` | `0.59` |
| wj-002 | classify_data_type | `request` | `verification` |
| wj-002 | requires_human_gate | `False` | `0.6` |
| wj-003 | classify_data_type | `request` | `evidence` |
| wj-004 | classify_data_type | `request` | `open_question` |
| wj-005 | select_artifact | `none_required` | `unclear_needs_review` |
| wj-006 | classify_data_type | `request` | `evidence` |
| wj-006 | select_artifact | `none_required` | `unclear_needs_review` |
| wj-006 | requires_human_gate | `True` | `0.31` |
| wj-007 | next_intent | `review` | `clarify` |
| wj-007 | select_artifact | `plan` | `unclear_needs_review` |
| wj-008 | classify_data_type | `result` | `evidence` |
| wj-008 | select_playbook | `none_required` | `browser_ui_verification` |
| wj-009 | requires_human_gate | `False` | `0.52` |
| wj-010 | classify_data_type | `work_item` | `plan` |
| wj-010 | next_intent | `execute` | `clarify` |
| wj-010 | select_artifact | `work_item_change` | `run_record` |
| wj-010 | requires_human_gate | `False` | `0.52` |
| wj-011 | classify_data_type | `other_needs_new` | `run_record` |
| wj-011 | next_intent | `research` | `verify` |
| wj-012 | classify_data_type | `other_needs_new` | `evidence` |
| wj-012 | select_playbook | `root_cause_analysis` | `research_and_synthesis` |
| wj-013 | classify_data_type | `other_needs_new` | `evidence` |
| wj-013 | select_playbook | `root_cause_analysis` | `research_and_synthesis` |
| wj-014 | classify_data_type | `other_needs_new` | `state_note` |
| wj-014 | next_intent | `research` | `verify` |
| wj-015 | classify_data_type | `other_needs_new` | `evidence` |
| wj-018 | next_intent | `research` | `clarify` |
| wj-018 | select_playbook | `root_cause_analysis` | `browser_ui_verification` |
| wj-019 | next_intent | `decide` | `clarify` |
| wj-020 | next_intent | `close` | `verify` |
| wj-020 | select_artifact | `result` | `work_item_change` |
| wj-020 | evidence_satisfies_exit | `True` | `0.26` |
| wj-022 | classify_data_type | `decision` | `open_question` |
| wj-023 | classify_data_type | `work_item` | `verification` |
| wj-023 | next_intent | `close` | `verify` |
| wj-023 | select_artifact | `result` | `verification_evidence` |
| wj-024 | classify_data_type | `request` | `state_note` |
| wj-024 | next_intent | `plan` | `clarify` |
| wj-025 | next_intent | `unclear_needs_review` | `clarify` |

## Errors

- wj-009 classify_data_type: HTTP 502: {"error":{"code":"UPSTREAM_INVALID_RESPONSE","message":"供应商响应不符合问题合同"},"meta":{"request_id":"cfac0265-07fc-42df-8418-c3b251fad58d"}}

## Noul raw probabilities (calibration data)

| Case | Judgment | Gold | P(true) | Verdict@0.5 |
|---|---|---|---|---|
| wj-001 | requires_human_gate | False | 0.590 | WRONG |
| wj-001 | evidence_satisfies_exit | False | 0.140 | correct |
| wj-002 | requires_human_gate | False | 0.600 | WRONG |
| wj-002 | evidence_satisfies_exit | False | 0.030 | correct |
| wj-003 | requires_human_gate | False | 0.340 | correct |
| wj-003 | evidence_satisfies_exit | False | 0.060 | correct |
| wj-004 | requires_human_gate | False | 0.070 | correct |
| wj-005 | requires_human_gate | False | 0.110 | correct |
| wj-006 | requires_human_gate | True | 0.310 | WRONG |
| wj-007 | requires_human_gate | True | 0.930 | correct |
| wj-007 | evidence_satisfies_exit | False | 0.060 | correct |
| wj-008 | requires_human_gate | False | 0.410 | correct |
| wj-008 | evidence_satisfies_exit | False | 0.060 | correct |
| wj-009 | requires_human_gate | False | 0.520 | WRONG |
| wj-009 | evidence_satisfies_exit | False | 0.040 | correct |
| wj-010 | requires_human_gate | False | 0.520 | WRONG |
| wj-011 | requires_human_gate | False | 0.270 | correct |
| wj-011 | evidence_satisfies_exit | False | 0.070 | correct |
| wj-012 | requires_human_gate | False | 0.160 | correct |
| wj-012 | evidence_satisfies_exit | False | 0.110 | correct |
| wj-013 | requires_human_gate | False | 0.260 | correct |
| wj-014 | requires_human_gate | False | 0.300 | correct |
| wj-014 | evidence_satisfies_exit | False | 0.060 | correct |
| wj-015 | requires_human_gate | False | 0.200 | correct |
| wj-015 | evidence_satisfies_exit | False | 0.090 | correct |
| wj-016 | requires_human_gate | False | 0.240 | correct |
| wj-016 | evidence_satisfies_exit | False | 0.260 | correct |
| wj-017 | requires_human_gate | False | 0.210 | correct |
| wj-018 | requires_human_gate | False | 0.150 | correct |
| wj-018 | evidence_satisfies_exit | False | 0.050 | correct |
| wj-019 | requires_human_gate | True | 0.700 | correct |
| wj-020 | requires_human_gate | False | 0.310 | correct |
| wj-020 | evidence_satisfies_exit | True | 0.260 | WRONG |
| wj-021 | requires_human_gate | False | 0.300 | correct |
| wj-022 | requires_human_gate | True | 0.900 | correct |
| wj-023 | requires_human_gate | False | 0.180 | correct |
| wj-023 | evidence_satisfies_exit | True | 0.570 | correct |
| wj-024 | requires_human_gate | False | 0.330 | correct |

## Caveats

- n=25 cases (137 judgment runs): small sample; accuracy percentages have wide confidence intervals. Treat as directional, not definitive.
- 5 of 25 cases are synthetic boundary cases; 20 are sourced from filed master-repo eval datasets (agent-behavior, incident-agent, issue-triage).
- Sparse targets: each judgment is scored only on cases where the case author deemed it meaningful, so per-judgment n varies (classify: 24 scored + 1 upstream error, next_intent: 25, select_artifact: 24, select_playbook: 24, requires_human_gate: 24, evidence_satisfies_exit: 14).
- Upstream gold conditioning flatters pipeline accuracy: a real pipeline would compound upstream errors.
- Noul threshold 0.50 is a neutral default, not the contracts' provisional thresholds (0.70 / 0.80); calibrate with more labels.
- Single model version (jev-1.13.0), single run per case: no temperature/variance measurement.

## Artifacts

- Raw results: `eval-run/results-2026-09-28.json` (in this checkout, untracked)
- Function configs: generated from PR #1 contracts at eval time; per-function id/version recorded in `eval-run/setup-out.json` (0600, untracked)