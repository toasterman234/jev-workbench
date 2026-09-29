#!/usr/bin/env python3
"""Jev Workbench Phase 1D evaluation: setup + run + score.

Phase 1D tests the rewritten judgment instructions (branch
work/work-judgment-instructions-v1d): instructions text only; vocabularies,
enums, review rules, and schemas untouched. Golds are unchanged from the
Phase 1C v2 suite, which is reused as-is.

Reads TYPESAFE_API_KEY ONLY from the process environment and only checks for
its presence (fail closed if absent). The key itself is consumed by the
workbench server from its own launch environment; this script never prints,
logs, or persists the key value or any client token.

Pipeline: bootstrap admin -> verify provider source=environment -> create the
six functions fresh from the v1d canonical configs (verified by draft checksum;
fail closed on mismatch) -> API client (token in memory only) -> Mode A
(component, gold upstream) + Mode B (end-to-end, predicted upstream) ->
score -> write results + mismatches (no tokens anywhere).

Resumable: every record is appended to checkpoint-phase1d.jsonl; a re-run
keeps records for fully-complete case-modes and re-runs the rest.
"""
import copy, hashlib, json, os, subprocess, sys, time, urllib.request, urllib.error

REPO = "/Users/bencharney/jev-workbench-pr2"
OUTDIR = os.path.join(REPO, "eval-run")
HOME = "/Users/bencharney/.jev-workbench-phase1d-eval"
PORT = 17424
BASE = f"http://127.0.0.1:{PORT}"
DATE = "2026-09-28"
CONFIG_BRANCH = "origin/work/work-judgment-instructions-v1d"
SUITE = "phase1c-v2"

# ---- fail closed: key must be present in the process environment ----
if not os.environ.get("TYPESAFE_API_KEY", "").strip():
    sys.exit("FATAL: TYPESAFE_API_KEY absent from process environment; refusing to run (fail closed).")
print("TYPESAFE_API_KEY present in environment (value never handled).", flush=True)

JUDGMENTS = ["classify_data_type", "next_intent", "select_artifact",
             "select_playbook", "requires_human_gate", "evidence_satisfies_exit"]
QID = {"classify_data_type": "primary_data_type", "next_intent": "next_intent",
       "select_artifact": "artifact_type", "select_playbook": "playbook_key",
       "requires_human_gate": "requires_human_gate",
       "evidence_satisfies_exit": "evidence_satisfies_exit"}
PRIM = {"classify_data_type": "choice", "next_intent": "choice",
        "select_artifact": "choice", "select_playbook": "choice",
        "requires_human_gate": "noul", "evidence_satisfies_exit": "noul"}
PROVISIONAL = {"requires_human_gate": 0.70, "evidence_satisfies_exit": 0.80}
ACTIVE_PLAYBOOKS = ["technical_project_exploration", "research_and_synthesis",
                    "decision_assessment", "implementation",
                    "root_cause_analysis", "browser_ui_verification"]


def req(method, path, body=None, headers=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if data is not None:
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), json.loads(resp.read().decode() or "null")


def req_cookie(method, path, body=None, cookie=None, csrf=None, timeout=90):
    h = {}
    if cookie:
        h["Cookie"] = cookie
    if csrf:
        h["x-csrf-token"] = csrf
    return req(method, path, body, h, timeout)


# ---------------- admin bootstrap ----------------
inst = json.load(open(os.path.join(HOME, "runtime/instance.json")))
ctl = inst["controlToken"]
st, _, b = req("POST", "/internal/open", None, {"Authorization": "Bearer " + ctl})
assert st == 200, st
bootstrap_token = b["url"].split("#bootstrap=")[1]
st, headers, b = req("POST", "/api/admin/bootstrap", {"token": bootstrap_token})
assert st == 200, st
csrf = b["csrf"]
# NOTE: req() dict-converts headers (case-sensitive); find Set-Cookie robustly
sc = next((v for k, v in headers.items() if k.lower() == "set-cookie"), None)
assert sc, "no Set-Cookie in bootstrap response (fail closed)"
cookie = sc.split(";")[0]
print("admin session bootstrapped", flush=True)

# ---------------- provider check: must be environment-sourced ----------------
st, _, status = req_cookie("GET", "/api/admin/status", cookie=cookie)
assert st == 200, st
prov = status.get("provider", {})
print("provider status:", json.dumps(prov), flush=True)
if prov.get("source") != "environment":
    sys.exit(f"FATAL: provider source is {prov.get('source')!r}, expected 'environment' (fail closed).")

# ---------------- canonical configs ----------------
config_branch_sha = subprocess.run(
    ["git", "-C", REPO, "rev-parse", CONFIG_BRANCH],
    capture_output=True, text=True, check=True).stdout.strip()
print("config branch SHA:", config_branch_sha, flush=True)

canonical, canonical_sha = {}, {}
for name in JUDGMENTS:
    out = subprocess.run(
        ["git", "-C", REPO, "show", f"{CONFIG_BRANCH}:examples/work-judgment/{name}.json"],
        capture_output=True, text=True, check=True).stdout
    canonical_sha[name] = hashlib.sha256(out.encode()).hexdigest()
    canonical[name] = json.loads(out)
    cfg = canonical[name]
    assert cfg["provider"] == "typesafe" and cfg["model"] == "jev-1.13.0", name
    print(f"canonical {name}: sha256={canonical_sha[name][:16]}...", flush=True)

# ---- Phase 1D: canonical configs carry the rewritten instructions. Strip only
# the top-level changelog for POSTing (the workbench schema 422-rejects it);
# review rules stay byte-identical and live.
posted, posted_sha = {}, {}
for n in JUDGMENTS:
    cfg = {k: v for k, v in canonical[n].items() if k != "changelog"}
    assert "changelog" not in cfg, n
    assert cfg["review"] == canonical[n]["review"], \
        f"review rules altered for {n} (fail closed)"
    posted[n] = cfg
    posted_sha[n] = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    print(f"posted {n}: sha256={posted_sha[n][:16]}... "
          f"(canonical {canonical_sha[n][:16]}...)", flush=True)

CONFIGS = posted

# ---------------- create functions fresh from v1d canonical configs ----------------
# Fresh isolated instance: create + publish the six functions from the posted
# configs (canonical minus changelog), verify draft checksums (fail closed).
# Idempotency: trash + permanently delete any previous functions with our keys
# (e.g. partial state from an interrupted run); function_key is UNIQUE.
st, _, existing = req_cookie("GET", "/api/admin/functions", cookie=cookie)
assert st == 200, st
for f in existing:
    if f.get("function_key") in JUDGMENTS:
        try:
            req_cookie("PATCH", f"/api/admin/functions/{f['id']}", {"trashed": True},
                       cookie=cookie, csrf=csrf)
            req_cookie("DELETE", f"/api/admin/functions/{f['id']}", cookie=cookie, csrf=csrf)
            print("removed leftover function:", f["function_key"], flush=True)
        except Exception as e:
            print("could not remove leftover", f.get("function_key"), e, flush=True)
funcs = []
previews = {"attempted": 6, "ok": 0}
for name in JUDGMENTS:
    cfg = CONFIGS[name]
    st, _, created = req_cookie("POST", "/api/admin/functions", cfg, cookie, csrf)
    assert st == 200, (name, st, json.dumps(created)[:300])
    fid, rev, chk = created["id"], created["draft_revision"], created["checksum"]
    smoke = {"content": "Smoke test: user asks to fix a typo in the README."}
    if name in ("select_artifact", "select_playbook"):
        smoke["next_intent"] = "clarify"
    last = None
    for attempt in (1, 2, 3):
        try:
            st, _, pv = req_cookie("POST", f"/api/admin/functions/{fid}/preview",
                                  {"config": cfg, "input": smoke}, cookie, csrf)
        except Exception as e:
            print(f"preview {name} attempt {attempt}: transport error {e}", flush=True)
            continue
        last = (st, pv)
        if st == 200 and pv.get("status") in ("ok", "needs_review"):
            print(f"preview ok for {name} (model={pv.get('meta', {}).get('model')})", flush=True)
            break
        print(f"preview {name} attempt {attempt}: http={st} {json.dumps(pv)[:200]}", flush=True)
    else:
        raise RuntimeError(f"preview failed for {name}: {last}")
    previews["ok"] += 1
    st, _, pub = req_cookie("POST", f"/api/admin/functions/{fid}/publish",
                           {"draft_revision": rev, "checksum": chk, "activate": True,
                            "note": "Phase 1D eval: instruction rewrite, model jev-1.13.0"},
                           cookie, csrf)
    assert st == 200, (name, st, json.dumps(pub)[:300])
    st, _, full = req_cookie("GET", f"/api/admin/functions/{fid}", cookie=cookie)
    assert st == 200, (name, st)
    assert full["active_version"] == 1, (name, full["active_version"])
    draft_sha = hashlib.sha256(json.dumps(full["draft"], sort_keys=True).encode()).hexdigest()
    assert draft_sha == posted_sha[name], f"draft checksum mismatch for {name} (fail closed)"
    print(f"created+published {name}: id={fid[:8]}... active_version=1 "
          f"draft_sha={draft_sha[:16]}... OK", flush=True)
    funcs.append({"key": name, "id": fid, "version": 1, "qid": QID[name],
                  "primitive": PRIM[name],
                  "canonical_sha256": canonical_sha[name],
                  "posted_sha256": posted_sha[name],
                  "verified_draft_sha256": draft_sha})

# ---------------- API client (token stays in memory only) ----------------
st, _, cli = req_cookie("POST", "/api/admin/clients",
                        {"name": "phase1d-eval-2026-09-28", "kind": "api",
                         "grants": [{"function_id": x["id"], "pinned_version": None}
                                    for x in funcs],
                         "official_invoke": True}, cookie, csrf)
assert st == 200, (st, json.dumps(cli)[:300])
CTOK = cli["token"]
print(f"API client created (id={cli['id']}); token held in memory only.", flush=True)

# manifest WITHOUT any token
manifest = {"date": DATE, "port": PORT, "suite": SUITE,
            "config_branch": CONFIG_BRANCH, "config_branch_sha": config_branch_sha,
            "canonical_sha256": canonical_sha,
            "posted_sha256": posted_sha,
            "note": "posted configs = canonical minus top-level changelog "
                    "(workbench schema 422-rejects it); review rules byte-identical and live",
            "functions_created": True,
            "functions": [{k: f[k] for k in ("key", "id", "version", "qid", "primitive",
                                             "canonical_sha256", "posted_sha256",
                                             "verified_draft_sha256")}
                          for f in funcs],
            "previews": previews}
json.dump(manifest, open(os.path.join(OUTDIR, "manifest-phase1d.json"), "w"), indent=2)
print("wrote manifest-phase1d.json (no tokens)", flush=True)

# ---------------- suite ----------------
import yaml
suite_doc = yaml.safe_load(open(os.path.join(OUTDIR, "suite-phase1c-v2.yaml")))
cases = suite_doc["cases"]
print(f"suite {suite_doc['suite_version']}: {len(cases)} cases", flush=True)
for c in cases:
    assert c["id"] and c["observation"]["summary"] and isinstance(c["expected"], dict)


def summary(case):
    return case["observation"]["summary"]


def classify_input(case):
    d = {"content": summary(case)}
    if case.get("source_type"):
        d["source_type"] = case["source_type"]
    return d


INTENT_FIELDS = ["current_lifecycle", "current_state", "known_artifacts",
                 "known_decisions", "blockers_or_unknowns",
                 "implementation_complete", "browser_or_ui_in_scope"]


def intent_input(case, object_type=None):
    d = {"content": summary(case)}
    ctx = case.get("context", {})
    for f in INTENT_FIELDS:
        if f in ctx:
            d[f] = ctx[f]
    if object_type:
        d["object_type"] = object_type
    return d


def artifact_input(case, next_intent, object_type=None):
    d = {"content": summary(case), "next_intent": next_intent}
    ctx = case.get("context", {})
    if object_type:
        d["object_type"] = object_type
    if "current_state" in ctx:
        d["current_state"] = ctx["current_state"]
    if "known_artifacts" in ctx:
        d["existing_artifacts"] = ctx["known_artifacts"]
    return d


def playbook_input(case, next_intent, artifact_type=None, object_type=None):
    d = {"content": summary(case), "next_intent": next_intent,
         "available_playbooks": ACTIVE_PLAYBOOKS}
    if artifact_type:
        d["artifact_type"] = artifact_type
    if object_type:
        d["object_type"] = object_type
    ctx = case.get("context", {})
    if "current_state" in ctx:
        d["current_state"] = ctx["current_state"]
    if "browser_or_ui_in_scope" in ctx:
        d["browser_or_ui_in_scope"] = ctx["browser_or_ui_in_scope"]
    if case.get("recurring_or_foundational_issue"):
        d["recurring_or_foundational_issue"] = True
    return d


def gate_input(case, next_intent=None):
    d = {"content": summary(case)}
    if next_intent:
        d["next_intent"] = next_intent
    for f in ["current_state", "proposed_action", "risk_or_consequence",
              "authority_context", "existing_approval"]:
        if f in case.get("gate_context", {}):
            d[f] = case["gate_context"][f]
    return d


def evidence_input(case):
    d = {"content": summary(case)}
    for f in ["current_state", "required_evidence", "available_evidence",
              "verification_summary", "browser_or_ui_in_scope",
              "browser_verification_present", "independent_verification_required",
              "independent_verification_present"]:
        if f in case.get("evidence_context", {}):
            d[f] = case["evidence_context"][f]
    return d


def invoke(fkey, inp):
    body = json.dumps({"input": inp}).encode()
    for attempt in (1, 2):
        try:
            r = urllib.request.Request(
                f"{BASE}/v1/functions/{fkey}/invoke", data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + CTOK})
            with urllib.request.urlopen(r, timeout=120) as resp:
                return resp.status, json.loads(resp.read().decode()), None
        except urllib.error.HTTPError as e:
            eb = e.read().decode()[:600]
            if attempt == 1 and e.code >= 500:
                time.sleep(3)
                continue
            return e.code, None, f"HTTP {e.code}: {eb}"
        except Exception as e:
            if attempt == 1:
                time.sleep(3)
                continue
            return -1, None, str(e)[:600]


counts = {"attempted": 0, "errored": 0, "scored": 0, "skipped_upstream_error": 0}
results = []
CKPT = os.path.join(OUTDIR, "checkpoint-phase1d.jsonl")

def mode_a_judgments(case):
    return [j for j in JUDGMENTS if j in case["expected"]]

# Resume: keep checkpoint records only for case-modes that are fully complete;
# cases missing any record will (re)run and their stale records are dropped.
done = set()
if os.path.exists(CKPT):
    kept_all = [json.loads(l) for l in open(CKPT) if l.strip()]
    have = {(r["mode"], r["case"], r["judgment"]) for r in kept_all}
    rerun = set()
    for c in cases:
        if not all(("A", c["id"], j) in have for j in mode_a_judgments(c)):
            rerun.add(("A", c["id"]))
        if not all(("B", c["id"], j) in have for j in JUDGMENTS):
            rerun.add(("B", c["id"]))
    kept = [r for r in kept_all if (r["mode"], r["case"]) not in rerun]
    with open(CKPT, "w") as fh:
        for r in kept:
            fh.write(json.dumps(r) + "\n")
    results.extend(kept)
    done = {(r["mode"], r["case"], r["judgment"]) for r in kept}
    print(f"checkpoint: {len(kept_all)} records on disk, keeping {len(kept)}, "
          f"re-running {len(rerun)} case-modes", flush=True)


def record(mode, case, jkey, inp, gold, upstream):
    counts["attempted"] += 1
    st, resp, err = invoke(jkey, inp)
    rec = {"mode": mode, "case": case["id"], "judgment": jkey,
           "gold": gold, "input": inp, "http": st, "upstream": upstream}
    if err is not None:
        counts["errored"] += 1
        rec.update({"status": "error", "predicted": None, "error": err})
    else:
        data = resp.get("data", {}) or {}
        rec.update({"status": resp.get("status"),
                    "predicted": data.get(QID[jkey]),
                    "review_reasons": resp.get("review_reasons", []),
                    "model": (resp.get("meta") or {}).get("model"),
                    "raw": resp})
    results.append(rec)
    with open(CKPT, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def gold_of(case, jkey):
    return case["expected"].get(jkey)


# ---------------- Mode A: component (gold upstream) ----------------
print("== Mode A: component ==", flush=True)
nA = 0
for case in cases:
    exp = case["expected"]
    if all(("A", case["id"], j) in done for j in mode_a_judgments(case)):
        print(f"[A] {case['id']} skipped (checkpoint)", flush=True)
        continue
    g = {j: gold_of(case, j) for j in JUDGMENTS}
    if "classify_data_type" in exp:
        nA += 1
        record("A", case, "classify_data_type", classify_input(case),
               exp["classify_data_type"], {})
    if "next_intent" in exp:
        nA += 1
        record("A", case, "next_intent",
               intent_input(case, object_type=g["classify_data_type"]),
               exp["next_intent"], {"object_type": g["classify_data_type"]})
    if "select_artifact" in exp:
        nA += 1
        record("A", case, "select_artifact",
               artifact_input(case, exp["next_intent"],
                              object_type=g["classify_data_type"]),
               exp["select_artifact"],
               {"next_intent": exp["next_intent"],
                "object_type": g["classify_data_type"]})
    if "select_playbook" in exp:
        nA += 1
        record("A", case, "select_playbook",
               playbook_input(case, exp["next_intent"],
                              artifact_type=g["select_artifact"],
                              object_type=g["classify_data_type"]),
               exp["select_playbook"],
               {"next_intent": exp["next_intent"],
                "artifact_type": g["select_artifact"],
                "object_type": g["classify_data_type"]})
    if "requires_human_gate" in exp:
        nA += 1
        record("A", case, "requires_human_gate",
               gate_input(case, next_intent=g["next_intent"]),
               exp["requires_human_gate"],
               {"next_intent": g["next_intent"]})
    if "evidence_satisfies_exit" in exp:
        nA += 1
        record("A", case, "evidence_satisfies_exit", evidence_input(case),
               exp["evidence_satisfies_exit"], {})
    print(f"[A] {case['id']} done", flush=True)
print(f"Mode A invoked: {nA}", flush=True)

# ---------------- Mode B: end-to-end (predicted upstream) ----------------
print("== Mode B: end-to-end ==", flush=True)
for case in cases:
    exp = case["expected"]
    if all(("B", case["id"], j) in done for j in JUDGMENTS):
        print(f"[B] {case['id']} skipped (checkpoint)", flush=True)
        continue
    pred, up_err = {}, {}

    def chain_step(jkey, inp, needs=()):
        for dep in needs:
            if pred.get(dep) is None:
                counts["skipped_upstream_error"] += 1
                return None, True
        rec = record("B", case, jkey, inp, exp.get(jkey),
                     {d: pred.get(d) for d in needs})
        if rec["status"] == "error":
            return None, True
        return rec["predicted"], False

    # 1. classify
    p, _ = chain_step("classify_data_type", classify_input(case))
    pred["classify_data_type"] = p
    # 2. next_intent <- predicted object_type
    p, _ = chain_step("next_intent",
                      intent_input(case, object_type=pred["classify_data_type"]),
                      needs=("classify_data_type",))
    pred["next_intent"] = p
    # 3. select_artifact <- predicted next_intent + object_type
    p, _ = chain_step("select_artifact",
                      artifact_input(case, pred["next_intent"],
                                     object_type=pred["classify_data_type"]),
                      needs=("next_intent", "classify_data_type"))
    pred["select_artifact"] = p
    # 4. select_playbook <- predicted next_intent + artifact + object_type
    p, _ = chain_step("select_playbook",
                      playbook_input(case, pred["next_intent"],
                                     artifact_type=pred["select_artifact"],
                                     object_type=pred["classify_data_type"]),
                      needs=("next_intent", "select_artifact",
                             "classify_data_type"))
    pred["select_playbook"] = p
    # 5. requires_human_gate <- predicted next_intent
    p, _ = chain_step("requires_human_gate",
                      gate_input(case, next_intent=pred["next_intent"]),
                      needs=("next_intent",))
    pred["requires_human_gate"] = p
    # 6. evidence_satisfies_exit (no upstream labels)
    p, _ = chain_step("evidence_satisfies_exit", evidence_input(case))
    pred["evidence_satisfies_exit"] = p

    # mark upstream_error on scored records: any fed upstream predicted value
    # that exists in gold and differs from gold
    for rec in results:
        if rec["mode"] != "B" or rec["case"] != case["id"] or rec["gold"] is None:
            continue
        flag, detail = False, {}
        for dep, fed in (rec.get("upstream") or {}).items():
            gj = {"classify_data_type": "classify_data_type",
                  "next_intent": "next_intent",
                  "select_artifact": "select_artifact"}.get(dep)
            if gj and gj in exp and fed != exp[gj]:
                flag = True
                detail[dep] = {"fed": fed, "gold": exp[gj]}
        rec["upstream_error"] = flag
        rec["upstream_detail"] = detail
    print(f"[B] {case['id']} done", flush=True)

# ---------------- scoring ----------------
per, mismatches, errors = {}, [], []
for r in results:
    key = (r["mode"], r["judgment"])
    per.setdefault(key, {"n": 0, "correct": 0, "brier": [],
                         "acc_at_050": 0, "acc_at_prov": 0, "n_noul": 0,
                         "review_triggers": {}})
    if r["status"] == "error" or r["gold"] is None:
        if r["status"] == "error":
            errors.append({"mode": r["mode"], "case": r["case"],
                           "judgment": r["judgment"], "error": r["error"]})
        continue
    v = per[key]
    v["n"] += 1
    gold, pred = r["gold"], r["predicted"]
    # review trigger accounting
    for reason in r.get("review_reasons") or []:
        rid = reason.get("rule") if isinstance(reason, dict) else str(reason)
        v["review_triggers"][rid] = v["review_triggers"].get(rid, 0) + 1
    if PRIM[r["judgment"]] == "choice":
        ok = (pred == gold)
    else:
        v["n_noul"] += 1
        if pred is None:
            errors.append({"mode": r["mode"], "case": r["case"],
                           "judgment": r["judgment"],
                           "error": "null prediction with ok status"})
            continue
        p = float(pred)
        v["brier"].append((p - (1.0 if gold else 0.0)) ** 2)
        if (p >= 0.50) == gold:
            v["acc_at_050"] += 1
        if (p >= PROVISIONAL[r["judgment"]]) == gold:
            v["acc_at_prov"] += 1
        ok = (p >= 0.50) == gold
    if ok:
        v["correct"] += 1
    else:
        mismatches.append({"mode": r["mode"], "case": r["case"],
                           "judgment": r["judgment"], "gold": gold,
                           "predicted": pred,
                           "p": (float(pred) if pred is not None and
                                 PRIM[r["judgment"]] == "noul" else None),
                           "review_status": r.get("status"),
                           "review_reasons": r.get("review_reasons"),
                           "upstream": r.get("upstream"),
                           "upstream_error": r.get("upstream_error", False),
                           "upstream_detail": r.get("upstream_detail", {}),
                           "model": r.get("model")})

scores = {}
for (mode, j), v in sorted(per.items()):
    n = v["n"]
    s = {"n": n, "correct": v["correct"],
         "accuracy": (v["correct"] / n) if n else 0.0,
         "review_triggers": v["review_triggers"]}
    if v["n_noul"]:
        b = v["brier"]
        s["brier"] = sum(b) / len(b)
        s["acc_at_0.50"] = v["acc_at_050"] / n
        s["acc_at_provisional"] = v["acc_at_prov"] / n
        s["provisional_threshold"] = PROVISIONAL[j]
    scores[f"{mode}/{j}"] = s

out = {"date": DATE, "suite": SUITE, "model": "jev-1.13.0",
       "counts": counts, "previews": manifest["previews"],
       "config_branch": CONFIG_BRANCH, "config_branch_sha": config_branch_sha,
       "canonical_sha256": canonical_sha,
       "posted_sha256": posted_sha,
       "scores": scores, "errors": errors,
       "results": results, "mismatches": mismatches}
json.dump(out, open(os.path.join(OUTDIR, "results-phase1d-2026-09-28.json"), "w"), indent=2)

mm = [{"id": f"{m['mode']}-{m['case']}-{m['judgment']}", **m}
      for m in mismatches]
json.dump(mm, open(os.path.join(OUTDIR, "mismatches-phase1d-2026-09-28.json"), "w"), indent=2)

counts = {"attempted": len(results),
          "errored": sum(1 for r in results if r["status"] == "error"),
          "scored": sum(1 for r in results
                        if r["status"] != "error" and r["gold"] is not None),
          "skipped_upstream_error": counts["skipped_upstream_error"]}
out["counts"] = counts
json.dump(out, open(os.path.join(OUTDIR, "results-phase1d-2026-09-28.json"), "w"), indent=2)
print("== counts:", json.dumps(counts), flush=True)
for k in sorted(scores):
    s = scores[k]
    line = f"{k}: {s['correct']}/{s['n']} = {s['accuracy']:.1%}"
    if "brier" in s:
        line += (f" | brier={s['brier']:.3f} acc@0.50={s['acc_at_0.50']:.1%} "
                 f"acc@{s['provisional_threshold']}={s['acc_at_provisional']:.1%}")
    if s["review_triggers"]:
        line += f" | review: {s['review_triggers']}"
    print(line, flush=True)
print(f"errors: {len(errors)}; mismatches: {len(mismatches)}", flush=True)
print("results + mismatches written (no tokens).", flush=True)
