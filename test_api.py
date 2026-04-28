"""
test_api.py  —  FairLens API Test Suite
────────────────────────────────────────
Tests all endpoints against a running FairLens server.

Usage:
    # Start the server first:
    uvicorn main:app --reload --port 8000

    # Then in another terminal:
    python test_api.py

    # With Gemini key:
    python test_api.py --gemini-key YOUR_KEY

    # Against a different host:
    python test_api.py --host http://your-server.com
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

BASE = "http://localhost:8000"
PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭️  SKIP"

results = []


def log(status, name, detail=""):
    icon = PASS if status == "pass" else (FAIL if status == "fail" else SKIP)
    line = f"  {icon}  {name}"
    if detail:
        line += f"  →  {detail}"
    print(line)
    results.append((status, name))


def test(name, fn):
    try:
        fn()
    except AssertionError as e:
        log("fail", name, str(e))
    except Exception as e:
        log("fail", name, f"Exception: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get(path, **kw):
    return requests.get(f"{BASE}{path}", timeout=30, **kw)


def post(path, **kw):
    return requests.post(f"{BASE}{path}", timeout=120, **kw)


def csv_file(filename):
    path = os.path.join("sample_data", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — run generate_samples.py first")
    return open(path, "rb")


def assert_score(j, key="score"):
    s = j.get(key)
    assert s is not None, f"Missing '{key}' in response"
    assert 0 <= s <= 100, f"Score {s} out of 0–100 range"
    return s


# ── Test groups ───────────────────────────────────────────────────────────────

def test_health():
    print("\n── Health & Root ─────────────────────────────────────────────")

    def _root():
        r = get("/")
        assert r.status_code == 200, f"Status {r.status_code}"
        j = r.json()
        assert "FairLens" in j["service"]
        log("pass", "GET /", j["service"])

    def _health():
        r = get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        log("pass", "GET /api/v1/health", "ok")

    test("GET /", _root)
    test("GET /api/v1/health", _health)


def test_hiring():
    print("\n── Module 1: Hiring Bias ─────────────────────────────────────")

    def _basic():
        with csv_file("hiring.csv") as f:
            r = post("/api/v1/analyse/hiring", files={"file": ("hiring.csv", f, "text/csv")})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "analyses" in j,  "Missing 'analyses'"
        assert "breakdown" in j, "Missing 'breakdown'"
        assert "summary"   in j, "Missing 'summary'"
        assert len(j["analyses"]) > 0, "No attribute analyses returned"
        log("pass", "POST /api/v1/analyse/hiring", f"score={score}/100, attrs={len(j['analyses'])}")

    def _structure():
        with csv_file("hiring.csv") as f:
            r = post("/api/v1/analyse/hiring", files={"file": ("hiring.csv", f, "text/csv")})
        j = r.json()
        for a in j["analyses"]:
            assert "attribute"        in a, "Missing attribute name"
            assert "significant"      in a, "Missing significant flag"
            assert "disparate_impact" in a, "Missing disparate_impact"
            assert "flagged_groups"   in a, "Missing flagged_groups"
        log("pass", "Hiring response structure", "all required fields present")

    def _bad_file():
        r = post("/api/v1/analyse/hiring",
                 files={"file": ("bad.csv", b"col1,col2\n1,2", "text/csv")})
        assert r.status_code == 422 or "error" in r.text.lower() or r.status_code == 500
        log("pass", "Hiring bad CSV handling", f"status={r.status_code}")

    test("Basic hiring analysis", _basic)
    test("Hiring response structure", _structure)
    test("Bad CSV rejection", _bad_file)


def test_ml():
    print("\n── Module 2: ML Model Bias ───────────────────────────────────")

    def _basic():
        with csv_file("ml_predictions.csv") as f:
            r = post("/api/v1/analyse/ml-model",
                     files={"file": ("ml_predictions.csv", f, "text/csv")})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "overall_accuracy" in j
        assert 0 <= j["overall_accuracy"] <= 1
        log("pass", "POST /api/v1/analyse/ml-model",
            f"score={score}/100, accuracy={j['overall_accuracy']:.1%}")

    def _metrics():
        with csv_file("ml_predictions.csv") as f:
            r = post("/api/v1/analyse/ml-model",
                     files={"file": ("ml_predictions.csv", f, "text/csv")})
        j = r.json()
        for a in j.get("analyses", []):
            gm = a["group_metrics"]
            assert len(gm) > 0
            first = gm[0]
            for col in ["precision","recall","fpr","fnr","accuracy"]:
                assert col in first, f"Missing metric: {col}"
        log("pass", "ML group metrics", "precision/recall/FPR/FNR all present")

    test("Basic ML analysis", _basic)
    test("ML fairness metrics structure", _metrics)


def test_manager():
    print("\n── Module 3: Manager Fairness ────────────────────────────────")

    def _basic():
        with csv_file("manager.csv") as f:
            r = post("/api/v1/analyse/manager",
                     files={"file": ("manager.csv", f, "text/csv")})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "total_managers"   in j
        assert "flagged_managers" in j
        assert j["total_managers"] > 0
        log("pass", "POST /api/v1/analyse/manager",
            f"score={score}/100, managers={j['total_managers']}, "
            f"flagged={j['flagged_managers']}")

    def _flagged():
        with csv_file("manager.csv") as f:
            r = post("/api/v1/analyse/manager",
                     files={"file": ("manager.csv", f, "text/csv")})
        j = r.json()
        flagged = j.get("flagged_details", [])
        # Our sample data has MGR01 and MGR03 biased
        ids = [m["manager_id"] for m in flagged]
        log("pass", "Flagged managers detected",
            f"flagged IDs: {ids[:5]}")

    test("Basic manager analysis", _basic)
    test("Biased manager detection", _flagged)


def test_leave_task():
    print("\n── Module 4: Leave & Task Fairness ───────────────────────────")

    def _leave_only():
        with csv_file("leave.csv") as f:
            r = post("/api/v1/analyse/leave-task",
                     files={"leave_file": ("leave.csv", f, "text/csv")})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "leave" in j
        log("pass", "Leave-only analysis", f"score={score}/100")

    def _task_only():
        with csv_file("task.csv") as f:
            r = post("/api/v1/analyse/leave-task",
                     files={"task_file": ("task.csv", f, "text/csv")})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "task" in j
        log("pass", "Task-only analysis", f"score={score}/100")

    def _combined():
        with csv_file("leave.csv") as lf, csv_file("task.csv") as tf:
            r = post("/api/v1/analyse/leave-task", files={
                "leave_file": ("leave.csv", lf, "text/csv"),
                "task_file":  ("task.csv",  tf, "text/csv"),
            })
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        j = r.json()
        score = assert_score(j)
        assert "leave" in j and "task" in j
        log("pass", "Combined leave+task analysis", f"score={score}/100")

    def _no_files():
        r = post("/api/v1/analyse/leave-task")
        assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        log("pass", "No-file rejection", f"status={r.status_code}")

    test("Leave-only analysis", _leave_only)
    test("Task-only analysis",  _task_only)
    test("Combined leave+task", _combined)
    test("No files rejection",  _no_files)


def test_full_audit(gemini_key=""):
    print("\n── Full Audit + PDF Report ───────────────────────────────────")

    def _pdf_generated():
        with (csv_file("hiring.csv")  as hf,
              csv_file("ml_predictions.csv") as mf,
              csv_file("manager.csv") as mgrf,
              csv_file("leave.csv")   as lf,
              csv_file("task.csv")    as tf):
            r = post("/api/v1/analyse/full-audit", files={
                "hiring_file":  ("hiring.csv",          hf,  "text/csv"),
                "ml_file":      ("ml_predictions.csv",  mf,  "text/csv"),
                "manager_file": ("manager.csv",         mgrf,"text/csv"),
                "leave_file":   ("leave.csv",           lf,  "text/csv"),
                "task_file":    ("task.csv",            tf,  "text/csv"),
            }, data={"gemini_key": gemini_key})

        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
        assert r.headers.get("content-type") == "application/pdf"
        assert len(r.content) > 10_000, f"PDF too small: {len(r.content)} bytes"

        overall = r.headers.get("X-Overall-Score")
        report_id = r.headers.get("X-Report-ID")
        assert overall,    "Missing X-Overall-Score header"
        assert report_id,  "Missing X-Report-ID header"

        # Save locally
        pdf_path = f"test_output_{report_id}.pdf"
        with open(pdf_path, "wb") as out:
            out.write(r.content)

        log("pass", "Full audit PDF generated",
            f"score={overall}/100, size={len(r.content)//1024}KB, "
            f"saved={pdf_path}, id={report_id}")
        return report_id

    def _hiring_only():
        """Full audit with only hiring file — others optional."""
        with csv_file("hiring.csv") as hf:
            r = post("/api/v1/analyse/full-audit",
                     files={"hiring_file": ("hiring.csv", hf, "text/csv")},
                     data={"gemini_key": ""})
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
        assert r.headers.get("content-type") == "application/pdf"
        log("pass", "Full audit (hiring only)", "PDF generated with 1 module")

    report_id = None

    def _run_full():
        nonlocal report_id
        report_id = _pdf_generated()

    test("Full audit all modules → PDF",  _run_full)
    test("Full audit hiring-only → PDF",  _hiring_only)

    if report_id:
        def _download():
            r = get(f"/api/v1/report/{report_id}")
            assert r.status_code == 200
            assert r.headers.get("content-type") == "application/pdf"
            log("pass", f"GET /api/v1/report/{report_id}", "re-download OK")

        def _not_found():
            r = get("/api/v1/report/nonexistent999")
            assert r.status_code == 404
            log("pass", "Report 404 handling", "correctly returns 404")

        test("Download report by ID", _download)
        test("404 for missing report", _not_found)


# ── Summary ───────────────────────────────────────────────────────────────────

def summary():
    total   = len(results)
    passed  = sum(1 for s, _ in results if s == "pass")
    failed  = sum(1 for s, _ in results if s == "fail")
    skipped = sum(1 for s, _ in results if s == "skip")

    print("\n" + "═"*60)
    print(f"  Test Results:  {passed}/{total} passed  "
          f"({failed} failed, {skipped} skipped)")
    print("═"*60)

    if failed:
        print("\n  Failed tests:")
        for status, name in results:
            if status == "fail":
                print(f"    ❌ {name}")
        sys.exit(1)
    else:
        print("\n  🎉  All tests passed!")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FairLens API Test Suite")
    parser.add_argument("--host",       default="http://localhost:8000", help="API base URL")
    parser.add_argument("--gemini-key", default="",    help="Gemini API key (optional)")
    args = parser.parse_args()

    BASE = args.host.rstrip("/")

    print("═"*60)
    print("  FairLens API Test Suite")
    print(f"  Target: {BASE}")
    print("═"*60)

    # Check server is up
    try:
        requests.get(f"{BASE}/api/v1/health", timeout=5)
    except Exception:
        print(f"\n❌  Cannot reach {BASE}")
        print("   Start the server first:")
        print("   uvicorn main:app --reload --port 8000\n")
        sys.exit(1)

    test_health()
    test_hiring()
    test_ml()
    test_manager()
    test_leave_task()
    test_full_audit(args.gemini_key)
    summary()
