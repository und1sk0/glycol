import time
import requests


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
