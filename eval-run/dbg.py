#!/usr/bin/env python3
"""Debug helper: bootstrap admin session, list functions, retry a preview."""
import json, sys, urllib.request, urllib.error

HOME = "/Users/bencharney/.jev-workbench-pr2-eval"
BASE = "http://127.0.0.1:17421"

def req(m, p, body=None, h=None):
    d = json.dumps(body).encode() if body is not None else None
    hh = dict(h or {})
    if d is not None:
        hh.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, timeout=120) as x:
            return x.status, json.loads(x.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:600]}

inst = json.load(open(HOME + "/runtime/instance.json"))
ctl = inst["controlToken"]
_, b = req("POST", "/internal/open", None, {"Authorization": "Bearer " + ctl})
tok = b["url"].split("#bootstrap=")[1]

# capture cookie manually
r = urllib.request.Request(BASE + "/api/admin/bootstrap",
                           data=json.dumps({"token": tok}).encode(),
                           method="POST",
                           headers={"Content-Type": "application/json"})
with urllib.request.urlopen(r, timeout=30) as resp:
    csrf = json.loads(resp.read().decode())["csrf"]
    cookie = resp.headers.get("Set-Cookie").split(";")[0]
AH = {"Cookie": cookie, "x-csrf-token": csrf}

_, fs = req("GET", "/api/admin/functions", None, AH)
print("functions:")
for f in fs:
    print(" ", f["function_key"], f["id"][:8], "active:", f.get("active_version"),
          "releases:", len(f.get("releases", [])))

# retry preview for select_artifact if it exists and has no release
tgt = [f for f in fs if f["function_key"] == "select_artifact"]
if tgt and not tgt[0].get("releases"):
    fid = tgt[0]["id"]
    _, full = req("GET", f"/api/admin/functions/{fid}", None, AH)
    draft = full["draft"]
    for attempt in (1, 2, 3):
        st, pv = req("POST", f"/api/admin/functions/{fid}/preview",
                     {"config": draft,
                      "input": {"content": "Smoke test: user asks to fix a typo in the README.",
                                "next_intent": "clarify"}}, AH)
        print(f"preview attempt {attempt}: http={st}",
              json.dumps(pv)[:400])
        if st == 200:
            break
