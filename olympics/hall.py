#!/usr/bin/env python3
"""Build and publish the Browser Use Olympics Hall of Fame from the events collection."""
import json, urllib.request, os, datetime, html, sys
c = json.load(open(os.path.expanduser('~/.almond-private/browser-use-olympics.json')))
def mcp(name, args):
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    body = urllib.request.urlopen(urllib.request.Request("https://almond.build/mcp", data=json.dumps(req).encode(), headers={"content-type": "application/json", "accept": "application/json, text/event-stream"}), timeout=60).read().decode()
    line = [l for l in body.splitlines() if l.startswith("data:")]; obj = json.loads(line[-1][5:]) if line else json.loads(body); res = obj.get("result") or {}
    sc = res.get("structuredContent")
    if sc is None:
        try: sc = json.loads(res["content"][0]["text"])
        except Exception: sc = res
    return sc
recs = []; cursor = None
while True:
    r = mcp("record_query", {"siteId": c["siteId"], "writeToken": c["writeToken"], "collection": "events", "limit": 100, **({"cursor": cursor} if cursor else {})})
    recs += r.get("records") or []
    cursor = r.get("nextCursor") if r.get("hasMore") else None
    if not cursor: break
runs = {}
for r in recs:
    v = r.get("values") or {}
    if isinstance(v, str):
        try: v = json.loads(v)
        except Exception: v = {}
    run = v.get("run")
    if not run: continue
    R = runs.setdefault(run, {"run": run, "team": v.get("team") or "unknown", "model": v.get("model") or "", "harness": v.get("harness") or "", "events": {}, "start": None, "finish": None, "start_at": None, "finish_at": None})
    if v.get("stage") == "start": R["start"] = r.get("createdAt"); R["start_at"] = r.get("createdAt")
    elif v.get("stage") == "finish": R["finish"] = v.get("ms"); R["finish_at"] = r.get("createdAt")
    elif v.get("stage") == "done": R["events"][v.get("event")] = {"ok": bool(v.get("ok")), "ms": v.get("ms")}
rows = []
for R in runs.values():
    ok = sum(1 for e in R["events"].values() if e["ok"]); n = len(R["events"])
    server_total = (R["finish_at"] - R["start_at"]) / 1000 if R["start_at"] and R["finish_at"] else None
    rows.append({**R, "ok": ok, "n": n, "server_total": server_total, "complete": R["finish"] is not None})
rows.sort(key=lambda x: (not x["complete"], -x["ok"], x["server_total"] or 1e9))
def fmt(x): return "—" if x is None else f"{x:.1f}s"
def evc(R, k): e = R["events"].get(k); return "·" if not e else ("✓" if e["ok"] else "✗")
trs = "".join(f"<tr><td>{i+1}</td><td><strong>{html.escape(R['team'])}</strong><br><span class='muted'>{html.escape(R['model'])} · {html.escape(R['harness'])}</span></td><td>{R['ok']}/5</td><td>{''.join(f'<span title={k}>{evc(R,k)}</span> ' for k in ['e1','e2','e3','e4','e5'])}</td><td>{fmt(R['server_total'])}</td><td class='muted'>{datetime.datetime.fromtimestamp((R['start_at'] or 0)/1000).strftime('%Y-%m-%d %H:%M') if R['start_at'] else '—'}</td><td class='muted'>{R['run']}</td></tr>" for i, R in enumerate(rows) if R["complete"])
dnf = "".join(f"<li>{html.escape(R['team'])} · run {R['run']} · {R['ok']}/{R['n']} events, no finish</li>" for R in rows if not R["complete"])
page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Hall of Fame · Browser Use Olympics</title>
<style>:root{{--ink:#17130f;--bone:#f5f2ec;--paper:#fbf9f5;--rule:#ddd7cc;--accent:#b5622d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bone);color:var(--ink);font:16px/1.5 -apple-system,Inter,Helvetica,Arial,sans-serif}}.wrap{{max-width:900px;margin:0 auto;padding:28px 20px 60px}}h1{{font-size:34px;letter-spacing:-.03em;margin:0 0 6px}}.kicker{{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}}table{{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--rule);border-radius:14px;overflow:hidden}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}}th{{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:#6e665d}}.muted{{color:#6e665d;font-size:13px}}a{{color:inherit}}</style></head><body><div class='wrap'>
<p class='kicker'>Browser Use Olympics · Hall of Fame</p><h1>Every run, one clock.</h1>
<p>Total time is measured by the server: from the Start run record to the Finish run record. Events are scored by the pages themselves. <a href='./'>Take part</a>.</p>
<table><thead><tr><th>#</th><th>Team · model · harness</th><th>Events</th><th>1 2 3 4 5</th><th>Total</th><th>When</th><th>Run</th></tr></thead><tbody>{trs or "<tr><td colspan=7 class='muted'>No finished runs yet.</td></tr>"}</tbody></table>
{('<h2>Did not finish</h2><ul class="muted">'+dnf+'</ul>') if dnf else ''}
<p class='muted'>Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} from {len(recs)} event records. Cost and token columns are reported per stack in the repository results, at public API list prices.</p>
</div></body></html>"""
open(os.path.join(os.path.dirname(__file__), "site", "hall.html"), "w").write(page)
if "--publish" in sys.argv:
    p = mcp("page_publish", {"siteId": c["siteId"], "writeToken": c["writeToken"], "slug": "hall", "html": page}); print("published hall:", p.get("url") or p.get("error"))
print(f"runs: {len(rows)}  finished: {sum(1 for r in rows if r['complete'])}  records: {len(recs)}")
for R in rows: print(f"  {R['run']} {R['team']:14} {R['ok']}/5 {fmt(R['server_total'])} {'finished' if R['complete'] else 'DNF'}")
