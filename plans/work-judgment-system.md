# Work Judgment System Plan

**Status:** planning only — no implementation is authorized by this document.  
**Repository baseline:** forked from `molis-ai/jev-workbench` at `75aeda4d92588b80ddfdcac527011ec14f197c3e`.  
**Purpose:** extend Jev Workbench into the human-facing judgment authoring and evaluation surface for deciding what work means and what should happen next, while preserving its existing role as a local, versioned Jev function workbench.

## 1. Problem statement

The target system needs to answer a recurring sequence of questions about work arriving from notes, Markdown, GitHub, projects, issues, Pi/Muse sessions, and other sources:

1. What is this thing?
2. What is the user's or system's intent?
3. What state is it currently in?
4. What state needs to become true?
5. What governed process should be used to get there?
6. What durable artifact should represent the result?
7. Which template and playbook apply?
8. What action should happen next?
9. Does the action require a human gate?
10. What evidence is required before the work can advance or close?
11. Did the agent actually do what it should have done?
12. What should be changed in future behavior when it did not?

The system should make these decisions explicit, testable, versioned, reviewable, and reusable by Pi and other agents.

## 2. Core principle

Do **not** make every low-level action create a new document.

Instead:

> Every governed action must create or update durable state and leave evidence appropriate to the lifecycle transition.

Examples:

- Explore creates or updates an Explore artifact.
- Research creates or updates evidence/research.
- Decide creates a Decision record.
- Plan creates or updates a Plan.
- Execute changes a WorkItem/implementation and records evidence.
- Verify creates verification evidence.
- Close records the final state and links the evidence that satisfied exit conditions.

The desired operating loop is:

```text
incoming item
    ↓
normalize / classify
    ↓
Jev judgments
    ↓
intent + desired state
    ↓
policy/lifecycle lookup
    ↓
artifact + template + playbook selection
    ↓
agent execution
    ↓
durable state + evidence
    ↓
verification
    ↓
behavior evaluation
    ↓
new cases / improved judgment definitions
```

## 3. Product boundary

### Jev Workbench should own

- Judgment function authoring.
- Noul / Choice / Score definitions.
- Preview and saved cases.
- Immutable published versions.
- Version-pinned clients.
- Pi/MCP/API access to published judgments.
- Human-readable grouping of related judgment functions.
- Explicit evaluation cases and expected outputs.
- Comparison of expected vs actual judgment behavior.
- Calibration and review surfaces for judgment quality.

### Jev Workbench should not become

- A general workflow/DAG engine.
- The authoritative project state store.
- A GitHub replacement.
- A filesystem automation engine.
- A generic connector hub.
- An arbitrary shell/SQL/script runner.
- A scheduler.
- The place that directly executes all playbooks.

This preserves the existing v1 contract, which explicitly excludes workflow DAGs and business-system automation.

### External systems should remain authoritative for

- Projects / WorkItems / Issues.
- Actual lifecycle state.
- Templates and playbooks.
- Artifact files.
- Evidence files and execution outputs.
- Agent orchestration.
- GitHub state.
- Runtime enforcement.

Jev Workbench should reference those concepts by stable IDs/keys and decide among them.

## 4. Domain distinctions

The following concepts must remain separate.

| Concept | Meaning | Example |
|---|---|---|
| Data type | What the incoming thing is | note, issue, session, project, artifact |
| Intent | Why work is being done | explore, research, decide, plan, execute, verify |
| Current state | Where the work is now | captured, exploring, planning, blocked |
| Desired state | What needs to become true | options-understood, plan-approved, verified |
| Artifact | Durable representation of work/result | Explore, Decision, Plan, Evidence |
| Template | Required structure of an artifact | explore-v1, plan-v2 |
| Playbook | Process for producing/advancing work | technical-research, RCA, UI-verification |
| Action | Immediate next operation | investigate, classify, draft, execute, verify |
| Evidence | Proof the process/result satisfies requirements | test, screenshot, source, diff |
| Eval | Whether the chosen/process behavior was correct | expected vs actual |

## 5. First intent vocabulary

Start small and keep the choices stable:

- `explore`
- `research`
- `decide`
- `plan`
- `execute`
- `verify`

Do not initially encode every special-case workflow as an intent. Specialization belongs in artifact/template/playbook selection.

Example:

```text
intent = verify
playbook = browser-ui-verification
artifact = VerificationEvidence
```

rather than creating a new intent named `browser_verify_ui`.

## 6. Judgment architecture

Do not create one giant `what_should_the_agent_do` function.

Use small versioned judgments with constrained choices.

### Work Intake judgment set

1. `classify_data_type` — Choice
2. `next_intent` — Choice
3. `desired_state` — Choice or constrained output
4. `select_artifact` — Choice
5. `select_template` — Choice
6. `select_playbook` — Choice

### Execution Governance judgment set

1. `requires_human_gate` — Noul
2. `allowed_to_execute` — Noul
3. `required_verification` — Choice
4. `evidence_satisfies_exit` — Noul
5. `work_risk` — Score

### Behavior Evaluation judgment set

1. `expected_intent` — Choice
2. `expected_next_action` — Choice
3. `process_violation` — Noul
4. `root_cause_category` — Choice
5. `behavior_change_needed` — Noul

A higher-level caller can assemble the individual outputs into a composite record. Jev Workbench itself does not need to make the individual questions dependent on each other.

## 7. Composite WorkJudgment envelope

The orchestration layer should be able to persist a record shaped approximately like:

```yaml
item_ref: github:master-repo#104
source_type: github_issue

classification:
  data_type: work_request
  current_state: captured

judgment:
  intent: explore
  desired_state: viable_options_understood
  artifact_type: Explore
  template_ref: explore-v1
  playbook_ref: technical-project-exploration
  next_action: inspect_primary_sources
  human_gate: false
  evidence_requirements:
    - primary_source_review
    - alternatives_considered

provenance:
  function_versions:
    next_intent: 3
    select_artifact: 2
    select_playbook: 4
  evaluated_at: ...
```

This composite record should be produced outside the core Jev function engine from versioned function outputs plus authoritative runtime context.

## 8. Templates vs playbooks

This distinction is required.

### Template

Defines **what the durable artifact must contain**.

Example Explore template:

- Question
- Current understanding
- Unknowns
- Hypotheses
- Options
- Evidence
- Constraints
- Findings
- Open questions
- Exit condition
- Promotion recommendation

### Playbook

Defines **how the agent should produce or advance that artifact**.

Example technical exploration playbook:

1. Check existing history and authority.
2. Check for retired/superseded work.
3. Inspect primary sources.
4. Identify alternatives.
5. Compare against requirements.
6. Record evidence.
7. Identify unresolved questions.
8. Evaluate exit conditions.
9. Recommend promotion, rejection, or continued exploration.

One artifact template may be served by multiple playbooks.

## 9. Historical Pi/Muse sessions as behavior data

The goal is not to train on entire raw sessions.

Extract **decision moments** where the agent had a meaningful choice.

Example:

```yaml
source:
  runtime: pi
  session_ref: ...
  event_ref: ...

context:
  request: fix the UI
  current_state: implementation_complete
  browser_available: true

actual:
  action: ran_unit_tests
  stopped_after: true

expected:
  intent: verify
  playbook: browser-ui-verification
  actions:
    - launch_application
    - inspect_in_browser
    - exercise_functionality
    - inspect_console
    - record_evidence

evaluation:
  correct: false
  category: process_violation
  rationale: browser-capable UI was not browser verified
```

The primary unit of training/evaluation is therefore a **labeled decision moment**, not a session transcript.

## 10. Privacy and storage boundary

The current Jev Workbench intentionally stores run metadata but not normal invocation inputs or answers. That behavior must remain intact.

Historical behavior data must therefore enter through an **explicit user-selected case/evaluation import path**.

Do not turn normal run history into a silent training corpus.

Recommended progression:

1. Use existing saved test cases for the first proof.
2. Add case metadata needed for source lineage and behavioral labels.
3. If test cases become overloaded, introduce a distinct `evaluation_cases` concept with explicit storage semantics.
4. Preserve the rule that normal API/MCP/Pi invocations do not persist raw business text.

Useful explicit metadata:

- source runtime
- source session/event reference
- source timestamp
- case kind: synthetic / historical / regression / calibration
- expected output
- actual observed action/result
- rationale
- reviewer
- tags
- lineage to superseded cases

## 11. UI direction

Preserve the existing quiet function workbench.

Do not add a generic KPI dashboard.

### Add: Judgment Sets

A Judgment Set is organizational metadata over functions, not a workflow DAG.

Example directory:

```text
Work Intake
  classify_data_type
  next_intent
  desired_state
  select_artifact
  select_template
  select_playbook

Execution Governance
  requires_human_gate
  allowed_to_execute
  required_verification
  evidence_satisfies_exit
  work_risk

Behavior Evaluation
  expected_intent
  expected_next_action
  process_violation
  root_cause_category
```

Requirements:

- A function may belong to one primary set initially.
- Sets do not change invocation semantics.
- Published function versions remain immutable.
- Grouping metadata must never silently change a published function contract.
- Directory search/filter continues to work.
- Archive/trash semantics remain function-level.

### Extend: Cases

Cases should eventually support:

- source/lineage metadata
- expected classification
- optional observed behavior
- rationale
- reviewer status
- regression/calibration tag
- batch run against draft or published version
- diff between expected and actual
- clear pass/fail/needs-review state

### Add later: Evaluation view

A focused comparison surface:

```text
Case
Expected
Actual
Version tested
Pass / mismatch / needs review
Reason
Previous version comparison
```

Do not fabricate an "accuracy" metric until a labeled evaluation set and metric definition exist.

## 12. Integration model

### Master Repo

Treat Master Repo as authority for:

- intent definitions
- lifecycle definitions
- artifact types
- template registry
- playbook registry
- evidence requirements
- gates
- supersession/retirement

Jev functions should consume a constrained set of currently valid choices derived from or synchronized with those definitions.

Initial implementation may use manually maintained stable keys. Do not block the first proof on live synchronization.

### Pi

Use the existing native Pi extension.

Pi should be able to:

1. list available judgment functions
2. describe a function
3. call a pinned version through a scoped client
4. receive typed output
5. hand that output to its governing runtime

The Pi extension should not directly read the Workbench database or Master Repo.

### Muse / other agents

Use MCP or HTTP unless a native integration is later justified.

### Behavior/eval tooling

Behavior tooling supplies:

- decision moments
- actual behavior
- human labels
- regression cases

Jev Workbench supplies:

- versioned judgment definitions
- case execution
- expected-vs-actual comparison
- calibration evidence

## 13. Implementation phases

### Phase 0 — lock contracts

Deliverables:

- this plan reviewed/accepted
- stable initial intent vocabulary
- initial data-type vocabulary
- initial artifact/template/playbook key lists
- definition of a decision moment
- privacy/storage rules
- explicit non-goals

Exit condition:

- no unresolved ambiguity about whether Workbench is a judgment layer or workflow runtime

### Phase 1 — prove Work Intake using existing primitives

Create functions using the current product before modifying architecture:

- `classify_data_type`
- `next_intent`
- `select_artifact`
- `select_playbook`
- `requires_human_gate`
- `evidence_satisfies_exit`

Create a small labeled case set.

Target:

- 20–30 representative cases
- include obvious cases and ambiguous boundary cases
- include at least several known historical Pi mistakes

No new UI architecture is required for this phase.

Exit condition:

- the functions are useful enough to demonstrate that decomposed judgments outperform a single open-ended "what next?" prompt

### Phase 2 — Judgment Sets

Add organizational grouping without changing invocation semantics.

Likely changes:

- migration for set metadata
- API CRUD for sets/membership
- left-rail grouping
- import/export support
- tests for archive/delete/membership behavior

Exit condition:

- Work Intake, Execution Governance, and Behavior Evaluation can be understood as coherent libraries in the UI

### Phase 3 — Behavioral case metadata

Extend saved cases or add a dedicated evaluation-case model.

Required capabilities:

- explicit import
- source lineage
- expected result
- observed behavior
- rationale/tags
- reviewer state
- batch evaluation
- regression comparison

Exit condition:

- a labeled Pi/Muse decision moment can be imported, reviewed, run against a judgment version, and traced back to its source

### Phase 4 — Session mining adapter

Build this outside the core Jev Workbench runtime.

Responsibilities:

- read Pi/Muse traces
- identify candidate decision points
- normalize context
- redact/trim irrelevant content
- produce proposed evaluation cases
- require explicit acceptance before Workbench stores raw case content

Start with offline import (JSON/JSONL). Avoid live watchers until the case model is proven.

Exit condition:

- 50–100 useful historical decision moments can be reviewed without importing entire sessions

### Phase 5 — Evaluation/calibration surface

Add:

- case suites
- version-vs-suite runs
- expected/actual diffs
- mismatch taxonomy
- version comparison
- calibration metrics only where mathematically justified

Examples:

- Choice classification accuracy/confusion by labeled set
- Noul Brier score / calibration
- regression count by version

Exit condition:

- a new judgment version can be evaluated before promotion and compared with the active version

### Phase 6 — Runtime decision contract

Define the external contract that Pi/governing runtime consumes.

Runtime flow:

```text
context
  ↓
call pinned judgment(s)
  ↓
assemble WorkJudgment
  ↓
lookup authoritative lifecycle/template/playbook
  ↓
gate
  ↓
execute
  ↓
record evidence
  ↓
verify
```

The runtime, not Jev Workbench, enforces the lifecycle.

Exit condition:

- one real work path from intake through verification uses published Jev judgments and records version provenance

### Phase 7 — broaden and automate

Only after the previous phases are verified:

- more intent subclasses if evidence supports them
- more playbooks
- live registry synchronization
- automated candidate extraction
- behavior-change proposals
- richer evaluation suites

## 14. First proof scenario

Use one narrow end-to-end example:

**Input:** a GitHub issue asking to investigate an unfamiliar tool.

Expected:

```text
data_type = work_request
next_intent = explore
desired_state = viable_options_understood
artifact = Explore
template = explore-v1
playbook = technical-project-exploration
human_gate = false
```

Then compare with:

- an issue that already has sufficient research and needs a Decision
- an approved plan that should Execute
- completed UI work that must Verify in-browser
- a recurring defect that should invoke RCA rather than another patch

This gives strong boundary cases with little infrastructure.

## 15. Verification requirements

No phase is complete because a write or tool call succeeded.

For code-bearing phases, verify at minimum:

- `pnpm typecheck`
- `pnpm test`
- `pnpm build`
- `pnpm test:e2e` when UI behavior changes
- read-back of stored records after mutations
- browser verification for UI changes
- functional browser interaction, not screenshot-only review
- no raw normal invocation payloads added to logs/runs
- published release immutability preserved
- Pi/MCP/HTTP contract compatibility preserved

For judgment-quality phases, verification must include a labeled case suite and versioned results. Model confidence alone is not evidence of business accuracy.

## 16. Risks

### Turning Workbench into the whole operating system

Mitigation: keep execution/lifecycle authority external.

### One giant judgment function

Mitigation: small constrained decisions with versioned outputs.

### Taxonomy explosion

Mitigation: six initial intents; specialize with artifacts/playbooks.

### Circular self-evaluation

Mitigation: retain human-labeled gold cases and explicit reviewer provenance.

### Silent training-data capture

Mitigation: explicit case import/save only; preserve current run privacy behavior.

### Stale Master Repo references

Mitigation: stable IDs plus version/supersession metadata; synchronization comes after the first proof.

### False certainty

Mitigation: ambiguous cases can route to review; probabilities are not treated as correctness.

### Upstream divergence

Mitigation: keep fork-specific additions modular and document every schema/UI extension so upstream changes can still be merged.

## 17. Immediate next actions after plan approval

1. Define the exact initial Choice keys for `classify_data_type`, `next_intent`, `select_artifact`, and `select_playbook`.
2. Create those functions in an unmodified Jev Workbench instance first.
3. Build 20–30 saved cases, including historical Pi decision moments.
4. Run and review the cases.
5. Record which limitations are genuinely UI/data-model problems versus judgment-definition problems.
6. Only then implement Judgment Sets and behavioral case metadata.

This sequence intentionally proves the behavioral model before modifying the product architecture.
