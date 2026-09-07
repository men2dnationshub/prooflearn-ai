from utils.health import get_health_status


def test_health_status() -> None:
    status = get_health_status()
    assert status["application"] == "ProofLearn AI"
    assert status["status"] == "healthy"
