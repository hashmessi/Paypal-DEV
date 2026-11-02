"""Phase 4: proof metrics, control tower API, demo run, admin/rate guards, LLM->money import boundary."""

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import guards
from app.main import app
from app.proof.runner import run_proof

APP = Path(__file__).resolve().parent.parent / "app"


def test_proof_metrics_are_measured_and_clean():
    r = run_proof()
    assert len(r["scenarios"]) >= 15
    assert all(s["passed"] for s in r["scenarios"]), [s["id"] for s in r["scenarios"] if not s["passed"]]
    m = {x["title"]: x for x in r["metrics"]}
    assert m["Detection rate"]["numerator"] == m["Detection rate"]["denominator"] > 0
    assert m["Unsafe-capture prevention"]["numerator"] == m["Unsafe-capture prevention"]["denominator"]
    assert m["False-block rate"]["numerator"] == 0 and m["False-block rate"]["denominator"] > 0
    assert m["Duplicate actions"]["numerator"] == 0


def test_refurbished_then_silent_followup_still_drifts():
    s9 = next(s for s in run_proof()["scenarios"] if s["id"] == "S09")
    assert s9["actual_outcome"] == "DRIFT" and s9["can_capture"] is False


def test_demo_run_creates_fresh_promise_each_time_and_tower_lists_it(client: TestClient):
    a = client.post("/demo/run", json={}).json()
    b = client.post("/demo/run", json={}).json()
    assert a["purchase_id"] != b["purchase_id"]
    t = client.get("/tower").json()
    ids = {p["id"] for p in t["promises"]}
    assert {a["purchase_id"], b["purchase_id"]} <= ids
    row = next(p for p in t["promises"] if p["id"] == a["purchase_id"])
    assert row["payment"]["state"] == "authorized" and row["payment"]["expiration_time"]
    assert row["status"] == "approved" and row["receipt_hash"]
    assert t["kpis"]["authorized_not_captured_count"] >= 2


def test_tower_shows_drift_after_refurbished_scenario(client: TestClient):
    pid = client.post("/demo/run", json={}).json()["purchase_id"]
    assert client.post(f"/fulfillment/scenarios/{pid}", json={"scenario": "refurbished"}).status_code == 200
    row = next(p for p in client.get("/tower").json()["promises"] if p["id"] == pid)
    assert row["gate_decision"]["outcome"] == "DRIFT"
    assert row["gate_decision"]["findings"][0]["severity"] == "DRIFT"
    assert any(e["type"] == "GATE_EVALUATED" for e in client.get("/events").json())


def test_seed_requires_admin_token(client: TestClient, monkeypatch):
    body = {"scenario": "happy_path"}
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "")
    assert client.post("/demo/scenarios", json=body, headers={"X-Admin-Token": ""}).status_code == 403
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "t0ken")
    assert client.post("/demo/scenarios", json=body).status_code == 403
    assert client.post("/demo/scenarios", json=body, headers={"X-Admin-Token": "wrong"}).status_code == 403
    assert client.post("/demo/scenarios", json=body, headers={"X-Admin-Token": "t0ken"}).status_code == 200


def test_llm_endpoint_rate_limited_per_ip(client: TestClient, monkeypatch):
    guards._hits.clear()
    monkeypatch.setattr("app.core.config.settings.LLM_RATE_LIMIT_PER_MIN", 2)
    codes = [client.post("/intent/extract", json={"instruction": "black headphones under $100 in 5 days"}).status_code for _ in range(3)]
    guards._hits.clear()
    assert codes[:2] == [200, 200] and codes[2] == 429


def _imports(path: Path) -> set:
    mods = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


def test_llm_code_has_no_import_path_to_money():
    """SEC-01: modules that touch LLMs or untrusted text cannot import payment/settlement code (transitively)."""
    forbidden = ("app.payments", "app.webhooks", "app.fulfillment", "app.api", "app.receipt.service")
    graph = {}
    for f in APP.rglob("*.py"):
        mod = ".".join(f.relative_to(APP.parent).with_suffix("").parts).removesuffix(".__init__")
        graph[mod] = _imports(f)
    seen, stack = set(), ["app.intent", "app.discovery", "app.drift.explainer"]
    stack += [m for m in graph if m.startswith(("app.intent.", "app.discovery."))]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        for dep in graph.get(m, ()):
            assert not dep.startswith(forbidden), f"{m} imports {dep}"
            stack.append(dep)


def test_capture_and_void_routes_only_exist_under_purchases_and_capture_is_gated():
    money = {p for p in app.openapi()["paths"] if p.rstrip("/").endswith(("/capture", "/void"))}
    assert money and all(p.startswith(("/purchases/", "/api/purchases/")) for p in money), money
    src = (APP / "api" / "payments.py").read_text(encoding="utf-8")
    assert "gateway.capture" not in src and "gateway.void" not in src  # routes go through PaymentsService only
