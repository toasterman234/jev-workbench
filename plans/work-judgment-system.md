# Work Judgment System Plan

**Status:** planning only — no implementation is authorized by this document.  
**Repository baseline:** forked from `molis-ai/jev-workbench` at `75aeda4d92588b80ddfdcac527011ec14f197c3e`.  
**Purpose:** extend Jev Workbench into the human-facing judgment authoring and evaluation surface for deciding what work means and what should happen next, while preserving its existing role as a local, versioned Jev function workbench.

### Planning artifacts

- [Seed registry](./seed-registry.yaml) — concrete initial vocabulary, authority/source metadata, fallbacks, and namespaced lifecycle states.
- [Judgment contracts](./judgment-contracts.yaml) — the first six constrained Choice/Noul contracts to prove before product implementation.

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
| Relationship type | How governed objects relate | depends_on, blocks, supersedes, produces |
| Guard type | Condition that must hold before a state change | evidence_required, approved_review |
| Gate type | External/human checkpoint before an action proceeds | human_approval, promotion_approval |
| Eval | Whether the chosen/process behavior was correct | expected vs actual |

## 5. Seed vocabulary: reuse before inventing

The initial registry should be seeded from **Master Repo vocabulary first**, then supplemented with selected **Cruxible operational primitives** where they fill a real gap. Jev Workbench should not create a parallel taxonomy when an existing authoritative concept already fits.

### Authority order

1. **Master Repo** — canonical authority for work/lifecycle/process vocabulary, artifact semantics, templates/playbooks, evidence requirements, lifecycle states, and promotion/supersession semantics.
2. **Cruxible agent-operation / project-domain** — reusable operational primitives for actors, work, reviews, risks, questions, state notes, project-domain objects, governed relationships, and guards/gates.
3. **Local Workbench registry** — editable catalog and proposal surface; may hold proposed terms that do not yet have an authoritative source.
4. **Ad hoc model output** — never authoritative. A model may suggest a proposed term, but it must enter through the registry lifecycle.

### Seed intent vocabulary

Use the process vocabulary already present in Master Repo:

- `intake`
- `clarify`
- `explore`
- `research`
- `decide`
- `plan`
- `execute`
- `verify`
- `review`
- `close`
- `promote`

These are **seeded defaults, not a permanently closed vocabulary**. New vocabulary can be proposed and added through the registry. Stable keys remain stable once referenced by a published function or durable record.

Do not encode every special-case workflow as a new intent. Specialization usually belongs in artifact/template/playbook selection.

Example:

```text
intent = verify
playbook = browser-ui-verification
artifact = Verification
```

rather than creating a new intent named `browser_verify_ui`.

### Seed object / data-type vocabulary

Prefer these existing concepts:

**Master Repo-derived**

- `Request`
- `IntakeRecord`
- `Project`
- `Explore`
- `WorkItem`
- `Decision`
- `Proposal`
- `Plan`
- `Evidence`
- `Result`
- `RunRecord`
- `Verification`
- `PromotionCandidate`
- `Artifact`
- `Template`
- `Playbook`
- `Source`
- `Finding`

**Cruxible-derived operational primitives**

- `Actor`
- `ReviewRequest`
- `Risk`
- `OpenQuestion`
- `StateNote`
- `Capability`
- `ProductArea`
- `RoadmapItem`
- `Milestone`
- `ReleaseLine`
- `SubjectRef`

The Workbench may also classify source-container types such as `Note`, `GitHubIssue`, `Session`, `MarkdownFile`, or `Repository` when that distinction is useful for routing.

### Seed action vocabulary

Start with:

- `classify`
- `route`
- `clarify`
- `investigate`
- `compare`
- `propose`
- `create`
- `update`
- `decompose`
- `execute`
- `test`
- `verify`
- `review`
- `approve`
- `reject`
- `defer`
- `close`
- `promote`
- `supersede`

### Seed relationship vocabulary

Reuse relationship meanings already present across Master Repo / Cruxible:

- `owned_by`
- `depends_on`
- `part_of`
- `spawned_from`
- `supersedes`
- `blocks`
- `mitigates`
- `answers`
- `constrains`
- `targets`
- `produces`
- `derived_from`
- `evidence_for`
- `uses`
- `governed_by`
- `runs_on`
- `resolves`
- `affects`

Where Cruxible has a more precise typed relationship such as `work_item_depends_on_work_item`, the registry can retain that source-specific key while exposing the simpler semantic label `depends_on` for human browsing.

### Seed evidence vocabulary

Start with:

- `Source`
- `Finding`
- `Observation`
- `TestResult`
- `BrowserVerification`
- `Screenshot`
- `Diff`
- `Commit`
- `RunRecord`
- `Review`
- `Approval`
- `Outcome`

### Seed guard / gate vocabulary

**Guards** protect a state transition:

- `evidence_required`
- `approved_review`
- `no_unresolved_blocker`
- `decision_required`
- `definition_of_done_satisfied`
- `independent_verification_required`
- `browser_verification_required`

**Gates** hold an external or consequential action:

- `human_approval`
- `approve_experiment`
- `promote_result`
- `promotion_approval`
- `merge_approval`

### Lifecycle states are namespaced

Do **not** create one global state enum. State meaning belongs to a lifecycle.

Seed from Master Repo:

```text
project:
  proposed → active → paused → completed → archived

explore:
  proposed → exploring → synthesized → decision-pending
  → promoted | parked | rejected

work_item:
  proposed → ready → in-progress → verification
  → accepted | changes-required | blocked → closed

decision:
  proposed → accepted | rejected → superseded

promotion:
  candidate → evaluated → approved → incorporated → propagated
```

Cruxible's broader operational lifecycle (`planned | active | blocked | watching | deferred | closed`) can be retained for Cruxible-native operational entities such as Risk, Capability, RoadmapItem, ReleaseLine, and Milestone. It should not replace the more specific Master Repo lifecycles.

Registry keys should therefore be namespaced where state ambiguity exists, for example:

```text
state.project.active
state.explore.exploring
state.work_item.verification
state.decision.accepted
state.promotion.approved
```

## 6. Extensible vocabularies and registries

The system must not assume that the initial data types, intents, artifact types, templates, playbooks, states, actions, or evidence types are complete.

Jev Workbench should eventually expose a human-editable **Registry** surface where the user can add, propose, revise, retire, and supersede vocabulary.

### Registry categories

Initial categories:

- Data Types / Object Types
- Intents
- Lifecycle Types
- Lifecycle States
- Artifact Types
- Templates
- Playbooks
- Actions
- Evidence Types
- Relationship Types
- Guard Types
- Gate Types

Additional categories may be introduced later without changing the meaning of existing entries.

### Registry entry shape

A registry entry should support approximately:

```yaml
category: playbook
key: technical-project-exploration
title: Technical Project Exploration
description: Explore an unfamiliar technical project before deciding whether to adopt it.
status: active
authority: master-repo
source_ref: master-repo:playbooks/technical-project-exploration
source_version: 1
aliases: []
supersedes: null
created_at: ...
updated_at: ...
```

Required concepts:

- **key** — machine-stable identifier; immutable after it is used in a published function or durable record
- **title** — human-readable name; editable
- **description/definition** — what the term means and when it applies
- **category** — data type, intent, template, playbook, etc.
- **status** — proposed, draft, active, retired, superseded
- **authority** — where the meaning is governed: master-repo, cruxible, local, or another explicit authority
- **source_ref** — optional pointer to the authoritative definition/file/entity
- **source_version** — optional pinned source version/revision
- **aliases** — alternate language/names that help classification
- **supersedes / superseded_by** — lineage when vocabulary changes

### Creating a missing template or playbook

The UI must support this path:

```text
select template/playbook
        ↓
nothing fits
        ↓
Create / propose new
        ↓
enter title
        ↓
optional key + description
        ↓
save as proposed/draft registry entry
        ↓
author the actual template/playbook later
        ↓
activate when definition/source exists
```

This lets the user capture an important concept immediately without falsely claiming the underlying template or playbook already exists.

Example:

```yaml
category: playbook
key: investigate-agent-behavior-regression
title: Investigate Agent Behavior Regression
status: proposed
source_ref: null
```

A proposed entry can represent **"we need a playbook with this title"**. It should not be treated as executable until the required definition/source and activation criteria are satisfied.

### "None fit" as an explicit judgment outcome

Judgments should not invent arbitrary new labels in production.

Where a vocabulary may be incomplete, Choice functions should include a stable fallback such as:

- `other_needs_new`
- `unclear_needs_review`

When selected, the Workbench can present the user with:

- choose a different existing entry
- create a proposed registry entry
- mark the case for taxonomy review

This produces useful evidence that the vocabulary is missing something.

### Published-version safety

Registry edits must **not silently mutate published Jev functions**.

Current Jev Choice criteria are part of an immutable release. Therefore:

1. a published function keeps the exact vocabulary snapshot it was published with
2. adding a registry entry does not change old releases
3. a draft may refresh from the current active registry
4. publishing the refreshed draft creates a new function version
5. provenance records which registry snapshot/entry keys were used

This preserves reproducibility.

### Registry UI

Add a **Vocabulary** or **Registry** destination to the workbench navigation.

Example:

```text
Vocabulary

Data Types
  Work Request
  Note
  GitHub Issue
  Session
  Evidence
  + Add

Templates
  Explore
  Decision
  Plan
  Verification Evidence
  + Add

Playbooks
  Technical Project Exploration
  Root Cause Analysis
  Browser UI Verification
  + Add
```

Creating an entry should be lightweight. At minimum the user can enter a **title** and category. The UI can derive a suggested key, but the user must be able to review it before the entry becomes active.

### Registry provenance and authority

Every seeded term should record where it came from.

Examples:

```yaml
category: object_type
key: work_item
title: Work Item
authority: master-repo
source_ref: master-repo:object/WorkItem
status: active
```

```yaml
category: object_type
key: review_request
title: Review Request
authority: cruxible-agent-operation
source_ref: cruxible:agent-operation/ReviewRequest
status: active
```

```yaml
category: playbook
key: investigate-agent-behavior-regression
title: Investigate Agent Behavior Regression
authority: local
status: proposed
source_ref: null
```

Authority is descriptive and enforceable metadata, not decoration. If an authoritative source marks an entry retired or superseded, the Workbench should surface that state before a new judgment version adopts it.

### Playbook versus executable procedure

Keep these concepts separate:

- **Playbook** — human/agent-readable process definition: what sequence, checks, decisions, evidence, and escalation rules should be followed.
- **Procedure** — bounded executable action compiled or adapted for a runtime.

A playbook may reference one or more procedures. Creating a playbook title does not imply executable automation exists.

### Registry versus authoritative artifacts

The registry describes and references a concept; it does not automatically create the full artifact behind it.

For example:

- a Template registry entry may point to a Markdown/YAML template in Master Repo
- a Playbook registry entry may point to its process definition
- a proposed entry may temporarily have no source
- activation should make missing definitions visible rather than hide them

This keeps vocabulary authoring fast while preserving the distinction between **naming a needed thing** and **actually defining that thing**.

## 7. Judgment architecture

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

## 8. Composite WorkJudgment envelope

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

## 9. Templates vs playbooks

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

## 10. Historical Pi/Muse sessions as behavior data

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

## 11. Privacy and storage boundary

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

## 12. UI direction

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

## 13. Integration model

### Master Repo

Treat Master Repo as the primary authority for:

- intent/process definitions
- lifecycle definitions and namespaced lifecycle states
- core work/artifact object types
- template registry
- playbook registry
- evidence requirements
- guards/gates
- promotion and supersession/retirement semantics
- required artifact trail

Seed the Workbench from the existing Master Repo trail:

```text
Request
→ Intake Record
→ Explore
  → Sources / Findings / Evidence
→ Decision / Proposal
→ Approved Plan
→ Work Item(s)
→ Verification
→ Result
→ Knowledge / Decision / New Work / Promotion Candidate
```

### Cruxible

Use selected Cruxible primitives as a secondary vocabulary source where Master Repo does not already provide a better canonical term.

Seed especially:

- Actor
- ReviewRequest
- Risk
- OpenQuestion
- StateNote
- SubjectRef
- Capability
- ProductArea
- RoadmapItem
- Milestone
- ReleaseLine
- typed ownership/dependency/blocking/answering/supersession relationships
- governed proposal semantics
- mutation guards and external gates

Do not wholesale replace Master Repo lifecycles with Cruxible's generic operational lifecycle. Preserve source-specific meanings and record source/authority on imported registry entries.

Jev functions should consume a constrained set of currently valid choices derived from or synchronized with those definitions.

The Workbench registry is the editable catalog/view of those choices. Master Repo may remain the authoritative source for fully defined templates, playbooks, lifecycles, and other governed objects. Registry entries can be proposed locally before a source definition exists, but activation and synchronization must preserve authority and lineage.

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

## 14. Implementation phases

### Phase 0 — lock contracts

Deliverables:

- this plan reviewed/accepted
- Master Repo + Cruxible vocabulary reuse map
- seeded initial intent vocabulary
- seeded initial object/data-type vocabulary
- seeded artifact/template/playbook key lists
- seeded relationship, guard, and gate vocabulary
- namespaced lifecycle state model
- registry authority/source contract
- registry entry contract and status lifecycle
- rules for proposing/activating/retiring/superseding vocabulary
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

### Phase 2 — Registries + Judgment Sets

Add editable vocabulary and organizational grouping without changing existing published invocation semantics.

Likely changes:

- registry-entry migration and status/lineage fields
- API CRUD for registry entries
- Vocabulary/Registry UI with category tabs and search
- lightweight "Add" flow that accepts at least category + title
- explicit proposed/draft/active/retired/superseded states
- "none fit → create proposed entry" flow
- validation that proposed entries are not treated as executable definitions
- migration for judgment-set metadata
- API CRUD for sets/membership
- left-rail judgment grouping
- import/export support for both registry and set metadata
- tests for version immutability, retirement/supersession, archive/delete/membership behavior

Exit condition:

- the user can add a new data type, artifact, template title, or playbook title without code changes
- missing vocabulary can be captured as proposed rather than silently invented
- published Jev versions remain unchanged when the registry changes
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

## 15. First proof scenario

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

## 16. Verification requirements

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

## 17. Risks

### Turning Workbench into the whole operating system

Mitigation: keep execution/lifecycle authority external.

### One giant judgment function

Mitigation: small constrained decisions with versioned outputs.

### Taxonomy explosion

Mitigation: six seeded intents; use registry proposals, review, retirement, aliases, and supersession instead of unconstrained label creation.

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

## 18. Immediate next actions after plan approval

1. Build the seed registry from Master Repo first and selected Cruxible primitives second, recording `authority`, `source_ref`, and source version where available.
2. Define the seeded Choice keys for `classify_data_type`, `next_intent`, `select_artifact`, and `select_playbook`, including `other_needs_new` / review fallbacks where appropriate.
3. Define the minimal RegistryEntry contract and proposed → active → retired/superseded lifecycle.
4. Define namespaced lifecycle states and ensure judgments receive the relevant lifecycle context instead of a global status enum.
5. Create the first judgment functions in an unmodified Jev Workbench instance.
6. Build 20–30 saved cases, including historical Pi decision moments and cases where none of the current vocabulary fits.
7. Run and review the cases.
8. Record which limitations are genuinely UI/data-model problems versus judgment-definition problems.
9. Implement the Registry/Vocabulary UI plus Judgment Sets.
10. Add behavioral case metadata after the registry behavior is verified.

This sequence intentionally proves the behavioral model before modifying the product architecture.
