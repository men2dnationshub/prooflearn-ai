from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "app.py", *sorted((ROOT / "pages").glob("*.py"))]

@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_page_starts_without_exception(page):
    app = AppTest.from_file(str(page)).run(timeout=20)
    assert not app.exception
    assert app.title
