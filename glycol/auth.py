import json
import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)


class OpenSkyAuth:
    """OAuth2 token manager for the OpenSky Network API."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._expires_at: float = 0.0

    def authenticate(self) -> bool:
        """Request a new bearer token. Returns True on success."""
        try:
            resp = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            expires_in = data.get("expires_in", 1800)
            # Refresh 60 seconds before actual expiry
            self._expires_at = time.time() + expires_in - 60
            return True
        except requests.RequestException:
            self._token = None
            return False

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def is_expired(self) -> bool:
        return time.time() >= self._expires_at

    def ensure_valid(self) -> bool:
        """Re-authenticate if the token is missing or near expiry."""
        if self._token is None or self.is_expired:
            return self.authenticate()
        return True

    def get_headers(self) -> dict:
        """Return Authorization headers, refreshing the token if needed."""
        self.ensure_valid()
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}


def load_credentials_from_file(
    credentials_path: Optional[Path] = None, data_dir: Optional[Path] = None
) -> Optional[Tuple[str, str]]:
    """
    Load credentials from a JSON file.

    Args:
        credentials_path: Path to credentials file. If None, uses default location.
        data_dir: Directory containing data files. If provided, credentials_path is relative to this.

    Returns:
        Tuple of (client_id, client_secret) if successful, None otherwise.
    """
    if credentials_path is None:
        if data_dir is None:
            # Default to glycol/data/credentials.json
            data_dir = Path(__file__).parent / "data"
        credentials_path = Path(data_dir) / "credentials.json"
    else:
        credentials_path = Path(credentials_path)

    if not credentials_path.exists():
        logger.info(f"Credentials file not found: {credentials_path}")
        return None

    try:
        with open(credentials_path, "r") as f:
            data = json.load(f)

        # Validate structure
        client_id = data.get("clientId")
        client_secret = data.get("clientSecret")

        if not client_id or not client_secret:
            logger.warning(f"Invalid credentials file structure: {credentials_path}")
            return None

        if not isinstance(client_id, str) or not isinstance(client_secret, str):
            logger.warning(f"Invalid credential types in: {credentials_path}")
            return None

        logger.info(f"Loaded credentials from: {credentials_path}")
        return (client_id, client_secret)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse credentials file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return None
