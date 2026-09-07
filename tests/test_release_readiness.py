from modules.release_readiness import readiness_json, run_readiness_checks

def test_repository_passes_automated_structure_checks():
    report = run_readiness_checks(".")
    assert report.status == "PROTOTYPE_VALIDATED"
    assert report.production_ready is False
    assert all(check.status != "FAIL" for check in report.checks)
    assert len(report.blockers) == 4

def test_readiness_report_is_json_serialisable():
    assert '"production_ready": false' in readiness_json(run_readiness_checks("."))
