#!/usr/bin/env python3
"""Phase 1 eval setup: bootstrap isolated instance, set provider key, create+publish
the six judgment functions from PR #1 contracts, create API client.
Writes eval-run/setup-out.json (0600). Never prints the TypeSafe key."""
import json, os, re, subprocess, sys, urllib.request

HOME = "/Users/bencharney/.jev-workbench-pr2-eval"
REPO = "/Users/bencharney/jev-workbench-pr2"
PORT = 17421
BASE = f"http://127.0.0.1:{PORT}"
OUTDIR = os.path.join(REPO, "eval-run")
os.makedirs(OUTDIR, exist_ok=True)

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

def req(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if data is not None:
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=90) as resp:
        return resp.status, json.loads(resp.read().decode() or "null")

# 1. control token -> bootstrap token -> admin session
inst = json.load(open(os.path.join(HOME, "runtime/instance.json")))
ctl = inst["controlToken"]
_, b = req("POST", "/internal/open", None, {"Authorization": "Bearer " + ctl})
token = b["url"].split("#bootstrap=")[1]
r = urllib.request.Request(BASE + "/api/admin/bootstrap",
                           data=json.dumps({"token": token}).encode(),
                           method="POST", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(r, timeout=30) as resp:
    csrf = json.loads(resp.read().decode())["csrf"]
    cookie = resp.headers.get("Set-Cookie").split(";")[0]
AH = {"Cookie": cookie, "x-csrf-token": csrf}
print("admin session bootstrapped")

# 2. provider key (loaded locally, never printed)
envtxt = open("/Users/bencharney/codex-scratch/jev-mermaid/.env").read()
key = re.search(r"(?m)^TYPESAFE_API_KEY=(.*)$", envtxt).group(1).strip().strip('"')
st, prov = req("PUT", "/api/admin/provider", {"key": key}, AH)
print("provider save http:", st, json.dumps(prov))
st, t = req("POST", "/api/admin/provider/test", {}, AH)
models = t.get("models", t) if isinstance(t, dict) else t
print("provider test http:", st, "models:", json.dumps(models)[:160])
assert st == 200, "provider test failed"

# 3. contracts -> function configs
import yaml
contracts = yaml.safe_load(sh(["git", "-C", REPO, "show", "pr1:plans/judgment-contracts.yaml"]))
shared_rules = contracts["shared_context"]["rules"]

# idempotency: trash + permanently delete any previous functions with our keys
st, existing = req("GET", "/api/admin/functions", None, AH)
for f in existing:
    if f.get("function_key") in contracts["functions"]:
        try:
            req("PATCH", f"/api/admin/functions/{f['id']}", {"trashed": True}, AH)
            req("DELETE", f"/api/admin/functions/{f['id']}", None, AH)
            print("removed leftover function:", f["function_key"])
        except Exception as e:
            print("could not remove leftover", f["function_key"], e)

def preview_with_retry(fid, cfg, smoke, fname):
    last = None
    for attempt in (1, 2, 3):
        try:
            st, pv = req("POST", f"/api/admin/functions/{fid}/preview",
                         {"config": cfg, "input": smoke}, AH)
        except Exception as e:
            print(f"preview {fname} attempt {attempt}: transport error {e}")
            continue
        last = (st, pv)
        if st == 200 and pv.get("status") in ("ok", "needs_review"):
            print(f"preview ok for {fname} "
                  f"(model={pv.get('meta', {}).get('model')})")
            return
        print(f"preview {fname} attempt {attempt}: http={st} "
              f"{json.dumps(pv)[:200]}")
    raise RuntimeError(f"preview failed for {fname}: {last}")

def input_schema(inp):
    props, reqd = {}, []
    for name, spec in inp.items():
        t = spec["type"]
        if t == "string":
            p = {"type": "string"}
        elif t == "boolean":
            p = {"type": "boolean"}
        elif t == "array":
            p = {"type": "array", "items": {"type": "string"}}
        else:
            raise ValueError("unknown input type " + t)
        if spec.get("description"):
            p["description"] = spec["description"]
        props[name] = p
        if spec.get("required"):
            reqd.append(name)
    return {"type": "object", "properties": props, "required": reqd,
            "additionalProperties": False}

def make_config(fname, f):
    qid = f["output"]["key"]
    prim = f["primitive"]
    instr = ("Shared context rules:\n" +
             "\n".join("- " + r for r in shared_rules) +
             "\n\n" + f["instructions"])
    if prim == "choice":
        q = {"type": "choice", "instructions": instr, "criteria": f["choices"]}
        src = f"/answers/{qid}/choice"
        outprop = {"enum": list(f["choices"].keys()) + [None]}
    elif prim == "noul":
        q = {"type": "noul", "instructions": instr, "criteria": f["criteria"]}
        src = f"/answers/{qid}/noul"
        outprop = {"type": ["number", "null"]}
    else:
        raise ValueError("unknown primitive " + prim)
    return {
        "format_version": 1,
        "key": fname,
        "name": f["title"],
        "description": f["purpose"],
        "when_to_use": f["when_to_use"],
        "provider": "typesafe",
        "model": "jev-1.13.0",
        "input_schema": input_schema(f["inputs"]),
        "state_mapping": {n: "/" + n for n in f["inputs"]},
        "questions": {qid: q},
        # Review routing intentionally not instantiated: it would null out the
        # raw prediction (on_review: null) for exactly the boundary labels this
        # eval measures. Accuracy is scored on raw judgment output.
        "review": {"match": "any", "rules": []},
        "output_mapping": {qid: {"source": src, "on_review": None}},
        "output_schema": {"type": "object", "properties": {qid: outprop},
                          "required": [qid], "additionalProperties": False},
    }

funcs = []
for fname, f in contracts["functions"].items():
    cfg = make_config(fname, f)
    st, created = req("POST", "/api/admin/functions", cfg, AH)
    assert st == 200, (st, json.dumps(created)[:300])
    fid, rev, chk = created["id"], created["draft_revision"], created["checksum"]
    # publish requires one successful preview run of the exact draft config
    smoke = {"content": "Smoke test: user asks to fix a typo in the README."}
    if fname in ("select_artifact", "select_playbook"):
        smoke["next_intent"] = "clarify"
    preview_with_retry(fid, cfg, smoke, fname)
    st, pub = req("POST", f"/api/admin/functions/{fid}/publish",
                  {"draft_revision": rev, "checksum": chk, "activate": True,
                   "note": "Phase 1 eval: PR #1 contracts, model jev-1.13.0"}, AH)
    assert st == 200, (st, json.dumps(pub)[:300])
    st, full = req("GET", f"/api/admin/functions/{fid}", None, AH)
    ver = full["active_version"]
    print(f"created+published {fname}: version={ver} id={fid[:8]}...")
    funcs.append({"key": fname, "id": fid, "version": ver, "qid": f["output"]["key"],
                  "primitive": f["primitive"]})

# 4. API client with grants for all six + official /v1/models grant
st, cli = req("POST", "/api/admin/clients",
              {"name": "pr2-eval-2026-09-28", "kind": "api",
               "grants": [{"function_id": x["id"], "pinned_version": None}
                          for x in funcs],
               "official_invoke": True}, AH)
assert st == 200, (st, json.dumps(cli)[:300])
print("client created:", cli["id"])

p = os.path.join(OUTDIR, "setup-out.json")
with open(p, "w") as fh:
    json.dump({"port": PORT, "functions": funcs,
               "client_token": cli["token"], "client_id": cli["id"]}, fh, indent=2)
os.chmod(p, 0o600)
print("wrote", p)
