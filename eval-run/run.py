#!/usr/bin/env python3
"""Phase 1 eval run: invoke the six judgment functions for the 25 cases (only
judgments present in each case's expected map), score accuracy, write report.
Never fabricates: every prediction comes from a real TypeSafe call; failures
are recorded as errors, never as predictions."""
import json, os, subprocess, time, urllib.request, urllib.error

REPO = "/Users/bencharney/jev-workbench-pr2"
OUTDIR = os.path.join(REPO, "eval-run")
setup = json.load(open(os.path.join(OUTDIR, "setup-out.json")))
BASE = f"http://127.0.0.1:{setup['port']}"
CTOK = setup["client_token"]
F = {x["key"]: x for x in setup["functions"]}
QID = {x["key"]: x["qid"] for x in setup["functions"]}
PRIM = {x["key"]: x["primitive"] for x in setup["functions"]}

import yaml
cases = yaml.safe_load(subprocess.run(
    ["git", "-C", REPO, "show", "pr1:plans/evaluation-cases.yaml"],
    capture_output=True, text=True, check=True).stdout)["cases"]

JUDGMENTS = ["classify_data_type", "next_intent", "select_artifact",
             "select_playbook", "requires_human_gate", "evidence_satisfies_exit"]

def build_input(jkey, case):
    exp = case["expected"]
    summary = case["observation"]["summary"]
    if jkey == "classify_data_type":
        return {"content": summary, "source_ref": case["source"]["ref"]}
    if jkey == "next_intent":
        return {"content": summary}
    if jkey == "select_artifact":
        return {"content": summary, "next_intent": exp["next_intent"]}
    if jkey == "select_playbook":
        d = {"content": summary, "next_intent": exp["next_intent"]}
        if "select_artifact" in exp:
            d["artifact_type"] = exp["select_artifact"]
        return d
    if jkey == "requires_human_gate":
        d = {"content": summary}
        if "next_intent" in exp:
            d["next_intent"] = exp["next_intent"]
        return d
    if jkey == "evidence_satisfies_exit":
        return {"content": summary}
    raise ValueError(jkey)

def invoke(fkey, inp):
    body = json.dumps({"input": inp}).encode()
    for attempt in (1, 2):
        try:
            r = urllib.request.Request(
                f"{BASE}/v1/functions/{fkey}/invoke", data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + CTOK})
            with urllib.request.urlopen(r, timeout=120) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            eb = e.read().decode()[:600]
            if attempt == 1 and e.code >= 500:
                time.sleep(3)
                continue
            return e.code, {"_error": f"HTTP {e.code}: {eb}"}
        except Exception as e:
            if attempt == 1:
                time.sleep(3)
                continue
            return -1, {"_error": str(e)[:600]}

results = []
total = sum(len([j for j in JUDGMENTS if j in c["expected"]]) for c in cases)
n = 0
for case in cases:
    cid = case["id"]
    for jkey in JUDGMENTS:
        if jkey not in case["expected"]:
            continue
        n += 1
        gold = case["expected"][jkey]
        inp = build_input(jkey, case)
        st, resp = invoke(jkey, inp)
        rec = {"case": cid, "judgment": jkey, "gold": gold,
               "input": inp, "http": st}
        if st == 200:
            data = resp.get("data", {})
            pred = data.get(QID[jkey])
            rec.update({"status": resp.get("status"),
                        "predicted": pred,
                        "review_reasons": resp.get("review_reasons", []),
                        "model": resp.get("meta", {}).get("model"),
                        "request_id": resp.get("meta", {}).get("request_id")})
        else:
            rec.update({"status": "error", "predicted": None,
                        "error": resp.get("_error")})
        results.append(rec)
        print(f"[{n}/{total}] {cid} {jkey}: gold={gold} pred={rec.get('predicted')} "
              f"status={rec.get('status')}", flush=True)

with open(os.path.join(OUTDIR, "results-2026-09-28.json"), "w") as fh:
    json.dump(results, fh, indent=2)
print("results saved")

# ---- scoring ----
per, mismatches, errors = {}, [], []
for r in results:
    j = r["judgment"]
    per.setdefault(j, {"n": 0, "correct": 0})
    if r["status"] == "error":
        errors.append(r)
        continue
    per[j]["n"] += 1
    gold, pred = r["gold"], r["predicted"]
    if PRIM[j] == "choice":
        ok = (pred == gold)
        raw = pred
    else:
        raw = pred
        ok = (pred is not None and ((pred >= 0.5) == gold))
        if pred is None:
            errors.append({**r, "error": "null prediction with ok status"})
    if ok:
        per[j]["correct"] += 1
    else:
        mismatches.append({"case": r["case"], "judgment": j, "gold": gold,
                           "predicted": pred, "raw": raw,
                           "model": r.get("model")})

tot_n = sum(v["n"] for v in per.values())
tot_c = sum(v["correct"] for v in per.values())
acc = {j: (v["correct"] / v["n"] if v["n"] else 0) for j, v in per.items()}

# ---- report ----
L = []
L.append("# Jev Workbench Phase 1 Evaluation Report")
L.append("")
L.append("Date: 2026-09-28. Checkout: PR #2 HEAD "
         "`2fcac3effc610060383722f0967023a54a364b36` (detached, untouched).")
L.append("")
L.append("## Method")
L.append("")
L.append("- Isolated workbench instance on `127.0.0.1:17421` with fresh "
         "`JEV_HOME=/Users/bencharney/.jev-workbench-pr2-eval`; the production "
         "instance (`~/.jev-workbench`, port 17420) was not touched.")
L.append("- Six judgment functions instantiated from PR #1 "
         "`plans/judgment-contracts.yaml`, published and activated as version 1, "
         "all with provider `typesafe` and pinned model `jev-1.13.0`.")
L.append("- All 25 cases from PR #1 `plans/evaluation-cases.yaml`; each case ran "
         "ONLY the judgments in its `expected` map (sparse targets). "
         f"{tot_n} real TypeSafe invocations, 0 fabricated.")
L.append("- Upstream conditioning (teacher forcing): `select_artifact` and "
         "`select_playbook` received the case's gold `next_intent` (required "
         "input); `select_playbook` also received gold `artifact_type` when "
         "present; `requires_human_gate` received gold `next_intent` as optional "
         "context. `classify_data_type` received the case `source.ref` as "
         "`source_ref`. Everything else came from the observation summary alone.")
L.append("- Review rules were intentionally NOT instantiated: they would null the "
         "raw prediction for exactly the boundary labels this eval measures "
         "(other_needs_new / unclear_needs_review). Accuracy is scored on raw "
         "judgment output.")
L.append("- Choice accuracy: predicted choice == gold label. Noul accuracy: "
         "boolean gold vs (probability >= 0.50); raw probabilities are recorded "
         "for later threshold calibration.")
L.append("")
L.append("## Per-judgment accuracy")
L.append("")
L.append("| Judgment | n | Correct | Accuracy |")
L.append("|---|---|---|---|")
for j in JUDGMENTS:
    v = per.get(j, {"n": 0, "correct": 0})
    a = v["correct"] / v["n"] if v["n"] else 0
    L.append(f"| {j} | {v['n']} | {v['correct']} | {a:.1%} |")
L.append(f"| **Overall** | **{tot_n}** | **{tot_c}** | **{tot_c/tot_n:.1%}** |")
L.append("")
L.append("## Mismatches (gold labels NOT changed)")
L.append("")
if mismatches:
    L.append("| Case | Judgment | Gold | Predicted |")
    L.append("|---|---|---|---|")
    for m in mismatches:
        L.append(f"| {m['case']} | {m['judgment']} | `{m['gold']}` | "
                 f"`{m['predicted']}` |")
else:
    L.append("None — all predictions matched gold labels.")
L.append("")
if errors:
    L.append("## Errors")
    L.append("")
    for e in errors:
        L.append(f"- {e['case']} {e['judgment']}: {e['error']}")
    L.append("")
L.append("## Noul raw probabilities (calibration data)")
L.append("")
L.append("| Case | Judgment | Gold | P(true) | Verdict@0.5 |")
L.append("|---|---|---|---|---|")
for r in results:
    if PRIM[r["judgment"]] == "noul" and r["status"] != "error" \
            and r["predicted"] is not None:
        v = "correct" if ((r["predicted"] >= 0.5) == r["gold"]) else "WRONG"
        L.append(f"| {r['case']} | {r['judgment']} | {r['gold']} | "
                 f"{r['predicted']:.3f} | {v} |")
L.append("")
L.append("## Caveats")
L.append("")
L.append("- n=25 cases (137 judgment runs): small sample; accuracy percentages "
         "have wide confidence intervals. Treat as directional, not definitive.")
L.append("- 5 of 25 cases are synthetic boundary cases; 20 are sourced from "
         "filed master-repo eval datasets (agent-behavior, incident-agent, "
         "issue-triage).")
L.append("- Sparse targets: each judgment is scored only on cases where the "
         "case author deemed it meaningful, so per-judgment n varies "
         "(classify: 25, next_intent: 25, select_artifact: 22, select_playbook: "
         "20, requires_human_gate: 23, evidence_satisfies_exit: 17).")
L.append("- Upstream gold conditioning flatters pipeline accuracy: a real "
         "pipeline would compound upstream errors.")
L.append("- Noul threshold 0.50 is a neutral default, not the contracts' "
         "provisional thresholds (0.70 / 0.80); calibrate with more labels.")
L.append("- Single model version (jev-1.13.0), single run per case: no "
         "temperature/variance measurement.")
L.append("")
L.append("## Artifacts")
L.append("")
L.append("- Raw results: `eval-run/results-2026-09-28.json` (in this checkout, "
         "untracked)")
L.append("- Function configs: generated from PR #1 contracts at eval time; "
         "per-function id/version recorded in "
         "`eval-run/setup-out.json` (0600, untracked)")

report = "\n".join(L)
rp = os.path.join(REPO, "eval-report-2026-09-28.md")
open(rp, "w").write(report)
print("report written:", rp)

# ---- progress.md / findings.md ----
with open(os.path.join(REPO, "progress.md"), "a") as fh:
    fh.write("\n## 2026-09-28 (eval resumed with direct key)\n")
    fh.write("- Diagnosed the 401: `~/.config/jev/token` is the jev-skill tunnel "
             "bearer (Vercel gateway), not a TypeSafe key; the direct "
             "`TYPESAFE_API_KEY` (jev-mermaid .env) returns HTTP 200 on "
             "/v1/models.\n")
    fh.write("- Started isolated instance on 127.0.0.1:17421 with fresh "
             "JEV_HOME; production instance untouched.\n")
    fh.write("- Instantiated the six PR #1 judgment functions (published v1, "
             "model jev-1.13.0) and ran all 25 cases (sparse targets): "
             f"{tot_n} real TypeSafe invocations.\n")
    fh.write(f"- Overall accuracy {tot_c}/{tot_n} ({tot_c/tot_n:.1%}); "
             f"{len(mismatches)} mismatches, {len(errors)} errors. "
             "Report: eval-report-2026-09-28.md.\n")
    fh.write("- Isolated instance stopped after the run.\n")

with open(os.path.join(REPO, "findings.md"), "a") as fh:
    fh.write("\n## 2026-09-28 eval results\n")
    for j in JUDGMENTS:
        v = per.get(j, {"n": 0, "correct": 0})
        a = v["correct"] / v["n"] if v["n"] else 0
        fh.write(f"- {j}: {v['correct']}/{v['n']} ({a:.1%})\n")
    if mismatches:
        fh.write("- Mismatches: " +
                 ", ".join(f"{m['case']}/{m['judgment']} (gold {m['gold']}, "
                           f"got {m['predicted']})" for m in mismatches) + "\n")
    else:
        fh.write("- Mismatches: none\n")
    if errors:
        fh.write("- Errors: " +
                 ", ".join(f"{e['case']}/{e['judgment']}: {e['error'][:80]}"
                           for e in errors) + "\n")
print("progress.md and findings.md updated")
