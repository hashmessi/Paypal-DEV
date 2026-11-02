"""Agent MCP gate: exactly 4 tools, no money surface, draft-only receipts (T-qw1-01/03)."""

import ast
import asyncio
import subprocess
import sys
from pathlib import Path

from app.mcp_server import server

BASE = Path(__file__).resolve().parent.parent
PKG = BASE / "app" / "mcp_server"
FORBIDDEN_NAMES = {"capture", "void", "authorize", "reconcile", "capture_authorization"}
FORBIDDEN_IMPORTS = ("app.payments", "app.webhooks", "app.api")


def _imports(tree: ast.AST):
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            yield n.module


def test_registers_exactly_four_tools():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert names == {"search_offers", "compile_promise", "get_gate_verdict", "get_replay"}


def test_source_has_no_money_surface():
    for f in PKG.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        assert not [m for m in _imports(tree) if m.startswith(FORBIDDEN_IMPORTS)], f.name
        bad = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
        }
        assert not (bad & FORBIDDEN_NAMES), (f.name, bad & FORBIDDEN_NAMES)


def test_runtime_module_graph_never_loads_payments():
    code = (
        "import sys, app.mcp_server.server;"
        "bad=[m for m in sys.modules if m.startswith(('app.payments','app.webhooks','app.api'))];"
        "print(bad); sys.exit(1 if bad else 0)"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=BASE, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_compile_promise_returns_pending_receipt_with_approval_url(db_session):
    r = asyncio.run(server._compile_promise(
        db_session, "new black over-ear headphones under $400, arrive within 5 days", _first_offer_id()))
    assert "error" not in r, r
    assert r["status"] == "draft" and r["receipt_hash"] and r["total_cents"] > 0
    assert r["approval_url"].endswith(f"/receipts/{r['purchase_id']}")


def _first_offer_id() -> str:
    return asyncio.run(server._search_offers("headphones", 1))["offers"][0]["offer_id"]


def test_gate_verdict_without_evaluation_is_empty(db_session):
    assert server._gate_verdict(db_session, "nope")["outcome"] is None
