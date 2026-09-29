#!/usr/bin/env python3
"""Generate eval-run/suite-phase1b-v1.yaml from the Phase 1 baseline suite.

Reads the baseline (PR #1 plans/evaluation-cases.yaml @ pr1), applies
Phase 1B deltas, writes the new suite version. Old gold labels are never
modified in place: deltas are documented per case with provenance.
"""
import yaml, copy, sys

BASE = yaml.safe_load(open("/tmp/phase1b-baseline-cases.yaml"))

HEADER = """# Work Judgment Phase 1B evaluation suite — version phase1b-v1
# Derived from the Phase 1 baseline suite (PR #1 plans/evaluation-cases.yaml @ pr1,
# 25 cases) WITHOUT modifying the baseline in place. All deltas vs the baseline
# are documented per case under `delta_vs_baseline` with provenance.
#
# Phase 1B changes:
# 1. Vocabulary: `incident` activated as a choice candidate for classify_data_type.
#    Provenance: baseline cases wj-011..wj-015 already carried
#    vocabulary_candidate {category: object_type, key: incident, title: Incident}
#    ("a useful type not yet active in the seed registry"). The Phase 1 eval showed
#    the model never predicted other_needs_new for these cases (it predicted
#    run_record/evidence/state_note instead), confirming a vocabulary gap rather
#    than a judgment failure. Their expected classify_data_type changes
#    other_needs_new -> incident IN THIS SUITE VERSION ONLY (baseline untouched).
# 2. Classification definition: classify_data_type judges the SEMANTIC OBJECT TYPE
#    of the item (what the thing is in domain terms), NOT its source/container.
#    The source/container type is recorded separately per case (`source_type`) and
#    passed as the `source_type` input.
# 3. next_intent inputs are enriched with the structured context the contract
#    already supports, ONLY where the source case supports it (see `context`).
#    Missing context stays missing; nothing is invented.
# 4. Five new synthetic evidence_satisfies_exit=true cases (wj-026..wj-030), each
#    clearly marked synthetic, so the boolean is not evaluated almost entirely
#    on negatives.
suite: work-judgment-phase1b
suite_version: phase1b-v1
baseline_suite: pr1:plans/evaluation-cases.yaml
composition:
  carried_over: 25
  new_synthetic: 5
  total: 30
vocabulary_amendments:
  - function: classify_data_type
    amendment: added choice `incident`
    definition: "An operational incident: an unplanned disruption, failure, outage, or urgent problem requiring diagnosis, response, and prevention."
    provenance: "baseline wj-011..wj-015 vocabulary_candidate (object_type/incident); Phase 1 eval confirmed the gap"
    review_rules: unchanged
classification_definition: "classify_data_type judges the SEMANTIC OBJECT TYPE of the item (what the thing is in domain terms), not its source/container. source_type is recorded separately per case and passed as input."
cases:
"""

# --- per-case source/container types (separate from semantic object type) ---
SOURCE_TYPE = {}
for i in range(1, 11):
    SOURCE_TYPE["wj-%03d" % i] = "agent-behavior eval case"
for i in range(11, 16):
    SOURCE_TYPE["wj-%03d" % i] = "incident-agent eval case"
for i in range(16, 21):
    SOURCE_TYPE["wj-%03d" % i] = "github issue"
for i in range(21, 31):
    SOURCE_TYPE["wj-%03d" % i] = "synthetic case"

# --- next_intent structured context, ONLY where the source case supports it ---
CONTEXT = {
    "wj-001": {
        "current_state": "User already approved the small reversible documentation fix ('fix gap'); agent re-asked for approval instead of executing.",
        "known_decisions": ["user approval for the documentation fix ('fix gap')"],
    },
    "wj-002": {
        "current_state": "Delivered as 'verified end-to-end' on API/HTTP evidence only; no real browser render observed; user saw an error.",
        "browser_or_ui_in_scope": True,
    },
    "wj-003": {
        "current_state": "Offered screenshot does not show the claimed nodes; DOM presence was mistaken for visible rendering.",
        "browser_or_ui_in_scope": True,
    },
    "wj-004": {
        "current_state": "User rejected the current visualization format; asks what other views/layouts/formats are available.",
    },
    "wj-005": {
        "current_state": "User says the diagram is bad and asks to 'see everything' without defining scope or detail level.",
        "blockers_or_unknowns": ["what 'everything' means", "desired level of detail"],
    },
    "wj-006": {
        "current_state": "Explicit one-canvas UX constraint; the requested drill-down would silently change it into seven separate pages.",
        "blockers_or_unknowns": ["user's choice: keep one canvas or accept seven pages"],
    },
    "wj-007": {
        "current_state": "Merge plan delivered as repo file + chat text; open decisions unresolved; plan not approved.",
        "known_artifacts": ["merge plan (repo file)", "merge plan (chat text)"],
        "blockers_or_unknowns": ["open decisions requiring the user's tap"],
    },
    "wj-008": {
        "current_state": "Agent repeatedly claims completion without tests, read-back, health checks, or other verification proof.",
        "implementation_complete": True,
    },
    "wj-009": {
        "current_state": "Static page marked successful; recipient-facing render broken; tone-choice requirement inverted.",
        "implementation_complete": True,
        "browser_or_ui_in_scope": True,
    },
    "wj-010": {
        "current_state": "Multi-phase plan approved with 'Go'; agent re-asks for approval at each internal phase boundary.",
        "known_decisions": ["multi-phase plan approved ('Go')"],
    },
    "wj-011": {
        "current_state": "Agent audit incorrectly reported existing vault folders as missing; doubled down after correction.",
    },
    "wj-012": {
        "current_state": "Agent calls intermittently time out around 120s; retry shortly afterward succeeds.",
    },
    "wj-013": {
        "current_state": "120s timeout resembles a prior incident, but evidence says the mechanism may differ.",
        "known_artifacts": ["prior incident record"],
    },
    "wj-014": {
        "current_state": "Sorter/onboarding failure recurred after prevention was supposedly implemented.",
        "known_artifacts": ["prior prevention implementation"],
    },
    "wj-015": {
        "current_state": "Timeout symptom returned; previously fixed retry race absent; earlier root cause likely wrong.",
    },
    "wj-016": {
        "current_state": "Small logging-only GitHub issue with a concrete requested code change; no unresolved design choice.",
    },
    "wj-017": {
        "current_state": "Open question: where a kanban/operations board fits, how it interacts with agents/workflows, what options exist.",
    },
    "wj-018": {
        "current_state": "Live VRP scan is stale; does not refresh when the user presses refresh.",
        "browser_or_ui_in_scope": True,
    },
    "wj-019": {
        "current_state": "Issue documents a systemic concurrent-agent coordination failure plus a proposal affecting shared work/branching behavior.",
        "known_decisions": ["proposal affecting shared work/branching behavior (documented in issue)"],
    },
    "wj-020": {
        "current_state": "Dagu shadow pilot Levels 0-2 complete; evidence linked; production migration deferred elsewhere.",
        "known_artifacts": ["pilot evidence (linked)"],
        "implementation_complete": True,
    },
    "wj-021": {
        "current_state": "Unfamiliar GitHub project; fit with agent runtime unknown; alternatives not yet compared.",
    },
    "wj-022": {
        "current_state": "Research and alternatives complete; two architecture options remain; user's choice required.",
        "known_artifacts": ["completed research and alternatives"],
        "blockers_or_unknowns": ["user's architecture choice"],
    },
    "wj-023": {
        "current_state": "UI implementation complete; real browser interaction passed; content visibly painted; console clean; screenshots/read-back match requirement.",
        "implementation_complete": True,
        "browser_or_ui_in_scope": True,
    },
    "wj-024": {
        "current_state": "Governed task needs a repeatable process for behavior-regression investigation; no active playbook covers it.",
        "blockers_or_unknowns": ["which governed process covers behavior-regression diagnosis and prevention tracking"],
    },
    # wj-025: intentionally no context — insufficient by design
}

# --- requires_human_gate enrichment, ONLY where the source case supports it ---
GATE_CONTEXT = {
    "wj-001": {"proposed_action": "execute the small reversible documentation fix", "existing_approval": True},
    "wj-006": {"proposed_action": "change the design from one canvas to seven pages",
               "risk_or_consequence": "materially changes an explicit UX constraint without user consent",
               "existing_approval": False},
    "wj-007": {"proposed_action": "proceed on the merge plan while decisions are still open", "existing_approval": False},
    "wj-010": {"proposed_action": "continue executing the approved multi-phase plan", "existing_approval": True},
    "wj-019": {"proposed_action": "adopt the proposal changing shared work/branching behavior",
               "risk_or_consequence": "changes shared agent behavior across concurrent agents",
               "existing_approval": False},
    "wj-022": {"proposed_action": "choose between the two architecture options", "existing_approval": False},
    "wj-028": {"proposed_action": "execute the approved migration plan", "existing_approval": True},
    "wj-030": {"proposed_action": "run the database migration in the 02:00-03:00 window", "existing_approval": True},
}

# --- evidence_satisfies_exit enrichment, ONLY where the source case supports it ---
EVIDENCE_CONTEXT = {
    "wj-002": {
        "required_evidence": ["real browser render observed"],
        "available_evidence": ["API/HTTP health evidence"],
        "verification_summary": "API/HTTP checks only; no browser render observed; user saw an error",
        "browser_or_ui_in_scope": True, "browser_verification_present": False,
    },
    "wj-003": {
        "required_evidence": ["screenshot showing claimed nodes visibly painted"],
        "available_evidence": ["screenshot (does not show claimed nodes)", "DOM presence"],
        "verification_summary": "DOM presence mistaken for visible rendering",
        "browser_or_ui_in_scope": True, "browser_verification_present": False,
    },
    "wj-007": {
        "required_evidence": ["approval of the merge plan"],
        "available_evidence": ["merge plan (repo file + chat text)"],
        "verification_summary": "plan exists but open decisions unresolved; not approved",
    },
    "wj-008": {
        "required_evidence": ["tests", "read-back", "health checks"],
        "available_evidence": ["agent's completion claim"],
        "verification_summary": "no verification proof offered",
    },
    "wj-009": {
        "required_evidence": ["recipient-facing render verified", "tone-choice requirement met"],
        "available_evidence": ["agent's success mark"],
        "verification_summary": "render broken; tone requirement inverted",
        "browser_or_ui_in_scope": True, "browser_verification_present": False,
    },
    "wj-011": {
        "required_evidence": ["root cause diagnosis"],
        "available_evidence": ["incorrect audit", "correction"],
        "verification_summary": "no diagnosis performed",
    },
    "wj-012": {
        "required_evidence": ["established mechanism for the timeouts"],
        "available_evidence": ["timeout observations", "successful retry"],
        "verification_summary": "mechanism unknown",
    },
    "wj-014": {
        "required_evidence": ["diagnosis of why prevention failed"],
        "available_evidence": ["recurrence observed"],
        "verification_summary": "no new diagnosis performed",
    },
    "wj-016": {
        "required_evidence": ["implemented change verified"],
        "available_evidence": ["none yet"],
        "verification_summary": "change not yet implemented",
    },
    "wj-018": {
        "required_evidence": ["refresh path diagnosed"],
        "available_evidence": ["stale scan observation"],
        "verification_summary": "mechanism unknown",
    },
    "wj-020": {
        "required_evidence": ["pilot completion evidence"],
        "available_evidence": ["linked pilot evidence (Levels 0-2 complete)"],
        "verification_summary": "Levels 0-2 complete per linked evidence",
    },
    "wj-023": {
        "required_evidence": ["browser interaction passed", "content visibly painted", "console clean", "screenshots/read-back match"],
        "available_evidence": ["browser interaction results", "screenshots/read-back"],
        "verification_summary": "real browser interaction passed; content painted; console clean",
        "browser_or_ui_in_scope": True, "browser_verification_present": True,
    },
}

# --- select_playbook flags, ONLY where supported ---
RECURRING = {"wj-014", "wj-019"}  # recurrence after supposed fix; systemic failure

# --- new synthetic evidence_satisfies_exit=true cases ---
NEW_CASES = [
    {
        "id": "wj-026", "synthetic": True,
        "source": {"kind": "synthetic", "ref": "synthetic:backup-migration-closeout"},
        "observation": {"summary": "Work item 'migrate nightly backup to new bucket' is done: the run log shows three consecutive successful nightly runs on the new bucket, the verification checklist is signed off, and the old bucket shows zero reads for seven days."},
        "context": {
            "current_state": "migration done; 3 successful nightly runs on new bucket; old bucket idle 7 days",
            "known_artifacts": ["run log (3 successful nightly runs)", "signed verification checklist"],
            "implementation_complete": True,
        },
        "evidence_context": {
            "required_evidence": ["successful runs on new bucket", "verification sign-off", "old bucket idle"],
            "available_evidence": ["run log (3 successful nightly runs)", "signed checklist", "old bucket zero reads for 7 days"],
            "verification_summary": "all exit evidence present and consistent",
        },
        "expected": {
            "classify_data_type": "work_item", "next_intent": "close",
            "select_artifact": "result", "select_playbook": "none_required",
            "requires_human_gate": False, "evidence_satisfies_exit": True,
        },
        "rationale": "Required evidence (successful runs, sign-off, idle old bucket) directly satisfies the migration exit conditions.",
        "provenance": "Phase 1B synthetic positive case for evidence_satisfies_exit (the baseline evaluated it almost entirely on negatives).",
    },
    {
        "id": "wj-027", "synthetic": True,
        "source": {"kind": "synthetic", "ref": "synthetic:research-question-answered"},
        "observation": {"summary": "The open question was which Postgres version the fleet runs. The research note cites the inventory export showing 15.4 on all 12 hosts, confirmed by the DBA in the thread."},
        "context": {
            "current_state": "research question answered with inventory export plus DBA confirmation",
            "known_artifacts": ["inventory export (12 hosts on 15.4)", "DBA confirmation"],
        },
        "evidence_context": {
            "required_evidence": ["fleet Postgres version from an authoritative source"],
            "available_evidence": ["inventory export (15.4 on 12 hosts)", "DBA confirmation"],
            "verification_summary": "two independent sources agree",
        },
        "expected": {
            "classify_data_type": "evidence", "next_intent": "close",
            "requires_human_gate": False, "evidence_satisfies_exit": True,
        },
        "rationale": "The evidence directly answers the research question with two independent sources; no further work is required.",
        "provenance": "Phase 1B synthetic positive case for evidence_satisfies_exit.",
    },
    {
        "id": "wj-028", "synthetic": True,
        "source": {"kind": "synthetic", "ref": "synthetic:plan-approved-decisions-resolved"},
        "observation": {"summary": "The migration plan's three open decisions were resolved in yesterday's review; the decision record is linked and the owner approved the plan this morning."},
        "context": {
            "current_state": "three open decisions resolved; owner approved the plan",
            "known_artifacts": ["decision record (linked)", "approved plan"],
            "known_decisions": ["three open decisions resolved in review", "owner approved the plan"],
        },
        "gate_context": {
            "proposed_action": "execute the approved migration plan",
            "existing_approval": True,
        },
        "evidence_context": {
            "required_evidence": ["decisions resolved", "owner approval"],
            "available_evidence": ["linked decision record", "owner approval"],
            "verification_summary": "all three decisions resolved; owner approved",
        },
        "expected": {
            "classify_data_type": "plan", "next_intent": "execute",
            "select_artifact": "plan", "select_playbook": "implementation",
            "requires_human_gate": False, "evidence_satisfies_exit": True,
        },
        "rationale": "Plan-approval exit conditions (decisions resolved + owner approval) are satisfied by linked evidence; execution is authorized.",
        "provenance": "Phase 1B synthetic positive case for evidence_satisfies_exit.",
    },
    {
        "id": "wj-029", "synthetic": True,
        "source": {"kind": "synthetic", "ref": "synthetic:release-qa-signoff"},
        "observation": {"summary": "The release checklist requires independent QA sign-off. QA signed off this morning and the staging smoke tests all pass; the release notes are published."},
        "context": {
            "current_state": "QA signed off; staging smoke tests pass; release notes published",
            "known_artifacts": ["QA sign-off", "staging smoke test results", "release notes"],
            "implementation_complete": True,
        },
        "evidence_context": {
            "required_evidence": ["independent QA sign-off", "staging smoke tests pass"],
            "available_evidence": ["QA sign-off", "staging smoke test results"],
            "verification_summary": "QA signed off; smoke tests pass",
            "independent_verification_required": True,
            "independent_verification_present": True,
        },
        "expected": {
            "classify_data_type": "verification", "next_intent": "close",
            "select_artifact": "result",
            "requires_human_gate": False, "evidence_satisfies_exit": True,
        },
        "rationale": "Independent verification required by the checklist is present and passing; the release can close.",
        "provenance": "Phase 1B synthetic positive case for evidence_satisfies_exit (also exercises independent-verification inputs).",
    },
    {
        "id": "wj-030", "synthetic": True,
        "source": {"kind": "synthetic", "ref": "synthetic:dba-approved-migration"},
        "observation": {"summary": "The consequential database migration required DBA approval before proceeding. The DBA approved it in the change ticket with a maintenance window of 02:00-03:00."},
        "context": {
            "current_state": "DBA approval recorded in change ticket; maintenance window 02:00-03:00",
            "known_decisions": ["DBA approved the migration (change ticket)"],
        },
        "gate_context": {
            "proposed_action": "run the database migration in the 02:00-03:00 window",
            "existing_approval": True,
        },
        "evidence_context": {
            "required_evidence": ["DBA approval"],
            "available_evidence": ["DBA approval in change ticket"],
            "verification_summary": "approval recorded with maintenance window",
        },
        "expected": {
            "classify_data_type": "decision", "next_intent": "execute",
            "select_artifact": "work_item_change", "select_playbook": "implementation",
            "requires_human_gate": False, "evidence_satisfies_exit": True,
        },
        "rationale": "The human-gate exit condition (DBA approval) is satisfied by ticket evidence; the approval is already present so no further gate is required.",
        "provenance": "Phase 1B synthetic positive case for evidence_satisfies_exit (gate already satisfied).",
    },
]

INCIDENT_CASES = {"wj-011", "wj-012", "wj-013", "wj-014", "wj-015"}


def main():
    cases = []
    for c in BASE["cases"]:
        cid = c["id"]
        nc = copy.deepcopy(c)
        nc["source_type"] = SOURCE_TYPE[cid]
        if cid in CONTEXT:
            nc["context"] = CONTEXT[cid]
        if cid in GATE_CONTEXT:
            nc["gate_context"] = GATE_CONTEXT[cid]
        if cid in EVIDENCE_CONTEXT:
            nc["evidence_context"] = EVIDENCE_CONTEXT[cid]
        if cid in RECURRING:
            nc["recurring_or_foundational_issue"] = True
        if cid in INCIDENT_CASES:
            old = nc["expected"]["classify_data_type"]
            assert old == "other_needs_new", (cid, old)
            nc["expected"]["classify_data_type"] = "incident"
            nc["delta_vs_baseline"] = (
                "expected.classify_data_type: other_needs_new -> incident. "
                "Provenance: baseline carried vocabulary_candidate "
                "{category: object_type, key: incident, title: Incident} "
                "('a useful type not yet active in the seed registry'); Phase 1 "
                "eval showed the model never predicted other_needs_new for these "
                "cases (predicted run_record/evidence/state_note), confirming a "
                "vocabulary gap. Incident activated as a choice candidate in "
                "this suite version only; baseline suite untouched."
            )
        # keep baseline helper keys (vocabulary_candidate, proposed_registry_entry)
        # as provenance; they are not eval inputs
        cases.append(nc)
    for nc in NEW_CASES:
        nc = copy.deepcopy(nc)
        nc["source_type"] = SOURCE_TYPE[nc["id"]]
        cases.append(nc)

    out = HEADER
    out += yaml.safe_dump(cases, sort_keys=False, allow_unicode=True, width=100)
    sys.stdout.write(out)
    # sanity
    print(f"# generated {len(cases)} cases", file=sys.stderr)


if __name__ == "__main__":
    main()
