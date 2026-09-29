# Findings

- PR #2 exact head verified locally: `2fcac3effc610060383722f0967023a54a364b36`.
- PR #1 contains `plans/evaluation-cases.yaml`, `plans/judgment-contracts.yaml`, `plans/seed-registry.yaml`, and `plans/work-judgment-system.md`.
- Node 24 is available at `/opt/homebrew/opt/node@24/bin/node`, version `v24.19.0`; it will be used for any future run.
- All six configs pin provider `typesafe` and model `jev-1.13.0`.
- The local Jev token file exists at `/Users/bencharney/.config/jev/token`, but a real request to `https://api.typesafe.ai/v1/models` returned HTTP 401 `authentication_error`; no usable provider configuration is available.
- Per the task constraint, no Workbench instance was started and no fabricated predictions were produced.

## 2026-09-28 eval results
- classify_data_type: 9/24 (37.5%)
- next_intent: 14/25 (56.0%)
- select_artifact: 18/24 (75.0%)
- select_playbook: 20/24 (83.3%)
- requires_human_gate: 19/24 (79.2%)
- evidence_satisfies_exit: 13/14 (92.9%)
- Mismatches: wj-001/classify_data_type (gold request, got session), wj-001/next_intent (gold execute, got clarify), wj-001/requires_human_gate (gold False, got 0.59), wj-002/classify_data_type (gold request, got verification), wj-002/requires_human_gate (gold False, got 0.6), wj-003/classify_data_type (gold request, got evidence), wj-004/classify_data_type (gold request, got open_question), wj-005/select_artifact (gold none_required, got unclear_needs_review), wj-006/classify_data_type (gold request, got evidence), wj-006/select_artifact (gold none_required, got unclear_needs_review), wj-006/requires_human_gate (gold True, got 0.31), wj-007/next_intent (gold review, got clarify), wj-007/select_artifact (gold plan, got unclear_needs_review), wj-008/classify_data_type (gold result, got evidence), wj-008/select_playbook (gold none_required, got browser_ui_verification), wj-009/requires_human_gate (gold False, got 0.52), wj-010/classify_data_type (gold work_item, got plan), wj-010/next_intent (gold execute, got clarify), wj-010/select_artifact (gold work_item_change, got run_record), wj-010/requires_human_gate (gold False, got 0.52), wj-011/classify_data_type (gold other_needs_new, got run_record), wj-011/next_intent (gold research, got verify), wj-012/classify_data_type (gold other_needs_new, got evidence), wj-012/select_playbook (gold root_cause_analysis, got research_and_synthesis), wj-013/classify_data_type (gold other_needs_new, got evidence), wj-013/select_playbook (gold root_cause_analysis, got research_and_synthesis), wj-014/classify_data_type (gold other_needs_new, got state_note), wj-014/next_intent (gold research, got verify), wj-015/classify_data_type (gold other_needs_new, got evidence), wj-018/next_intent (gold research, got clarify), wj-018/select_playbook (gold root_cause_analysis, got browser_ui_verification), wj-019/next_intent (gold decide, got clarify), wj-020/next_intent (gold close, got verify), wj-020/select_artifact (gold result, got work_item_change), wj-020/evidence_satisfies_exit (gold True, got 0.26), wj-022/classify_data_type (gold decision, got open_question), wj-023/classify_data_type (gold work_item, got verification), wj-023/next_intent (gold close, got verify), wj-023/select_artifact (gold result, got verification_evidence), wj-024/classify_data_type (gold request, got state_note), wj-024/next_intent (gold plan, got clarify), wj-025/next_intent (gold unclear_needs_review, got clarify)
- Errors: wj-009/classify_data_type: HTTP 502: {"error":{"code":"UPSTREAM_INVALID_RESPONSE","message":"供应商响应不符合问题合同"}
