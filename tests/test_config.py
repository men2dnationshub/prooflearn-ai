from modules.config import APP_NAME, APP_VERSION, SUPPORTED_FILE_TYPES


def test_application_identity() -> None:
    assert APP_NAME == "ProofLearn AI"
    assert APP_VERSION == "0.12.0"


def test_initial_file_types() -> None:
    assert SUPPORTED_FILE_TYPES == ("docx", "pdf", "txt")
