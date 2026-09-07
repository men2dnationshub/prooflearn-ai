from modules.deployment import deployment_json, run_deployment_checks


def test_repository_is_deployable_as_a_controlled_prototype():
    report = run_deployment_checks(".")
    assert report.status == "DEPLOYABLE_PROTOTYPE"
    assert report.demo_deployable is True
    assert report.production_ready is False
    assert all(check.status == "PASS" for check in report.checks)


def test_deployment_report_is_json_serialisable():
    output = deployment_json(run_deployment_checks("."))
    assert '"demo_deployable": true' in output
    assert '"production_ready": false' in output
