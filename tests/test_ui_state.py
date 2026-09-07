from ui.shared import ReportItem

def test_report_item_metadata():
    item = ReportItem("analysis", "Analysis", "analysis.json", "application/json", "{}", "Assignment")
    assert item.filename.endswith(".json") and item.category == "Assignment"
