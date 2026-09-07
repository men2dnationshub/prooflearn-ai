"""Application health information."""

from modules.config import APP_NAME, APP_VERSION


def get_health_status() -> dict[str, str]:
    """Return a small status payload for diagnostics and deployment checks."""
    return {"application": APP_NAME, "version": APP_VERSION, "status": "healthy"}
