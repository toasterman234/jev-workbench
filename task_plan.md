# Jev Workbench Phase 1 evaluation

## Goal
Evaluate the six Work Judgment v1 configs against the 25-case suite from PR #1 at PR #2 head, using one fixed Jev model version, without UI/registry/data-model/workflow changes.

## Phases
- [complete] 1. Verify checkout, runtime, suite, contracts, and provider prerequisites
- [blocked] 2. Start isolated Workbench instance and instantiate six configs
- [blocked] 3. Run only applicable judgment targets with one pinned model
- [blocked] 4. Analyze results and write concise report
- [pending] 5. Record durable evidence on PR #2

## Decisions
| Decision | Rationale |
|---|---|
| Use `/Users/bencharney/jev-workbench-pr2` | Separate checkout; leave upstream untouched |
| Stop if real Jev/TypeSafe provider configuration is unavailable | Never fabricate model results |
| Do not change gold labels | Mismatches are reported separately for review |

## Errors
| Attempt | Error | Resolution |
|---|---|---|
| 1 | Node 24 executable not found; system Node is 26.7.0 | Resolved: `/opt/homebrew/opt/node@24/bin/node` is available and reports v24.19.0 |
| 2 | TypeSafe `/v1/models` with local Jev token returned HTTP 401 authentication_error | Blocked: no usable real provider configuration; stop before evaluation |

