
import os
from pathlib import Path

from fastapi import HTTPException, Query


def require_allowed_repository(
    repo_path: str = Query(..., description="Repository folder to scan"),
) -> None:
    """
    Make sure the requested repository is inside
    the configured allowed workspace.
    """

    # Default: the folder containing security.py
    default_root = Path(__file__).resolve().parent

    # Allow the user to configure a different workspace.
    configured_root = os.getenv("REPOLENS_ALLOWED_ROOT")

    if configured_root:
        allowed_root = Path(configured_root).expanduser().resolve()
    else:
        allowed_root = default_root

    # Normalize the requested repository path.
    requested_repo = Path(repo_path).expanduser().resolve()

    # Reject repositories outside the allowed workspace.
    if not requested_repo.is_relative_to(allowed_root):
        raise HTTPException(
            status_code=403,
            detail="Repository is outside the allowed workspace.",
        )
