"""Headless UI smoke test. Requires pip install -e '.[web]'."""
from pathlib import Path
from streamlit.testing.v1 import AppTest


def main():
    app = Path(__file__).resolve().parents[1] / "src" / "researchmind_yulan" / "webapp.py"
    at = AppTest.from_file(str(app), default_timeout=20).run()
    if at.exception:
        raise AssertionError("Initial render error: " + repr(at.exception))
    at.button[0].click().run()
    if at.exception:
        raise AssertionError("Offline demo UI error: " + repr(at.exception))
    result = at.session_state["result"]
    assert result.evidence and result.claim_graph.links, "Missing backend outputs"
    print("Web AppTest: passed; evidence:", len(result.evidence),
          "claims:", len(result.claim_graph.claims),
          "gaps:", len(result.gaps))


if __name__ == "__main__":
    main()
