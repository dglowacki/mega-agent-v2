"""
MCP Authentication Module

Supports:
- OAuth2 Authorization Code flow (for Claude Desktop)
- API Key authentication (for programmatic access)
- Bearer token authentication
"""

import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Storage paths
DATA_DIR = Path("/home/ec2-user/mega-agent2/data")
TOKEN_STORAGE_FILE = DATA_DIR / "oauth_tokens.json"
API_KEYS_FILE = DATA_DIR / "api_keys.json"
OAUTH_PASSWORD_FILE = DATA_DIR / "oauth_password.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TokenData:
    """OAuth token data."""
    client_id: str
    scope: str
    expires_at: datetime
    created_at: datetime


class AuthManager:
    """
    Authentication manager for MCP server.

    Supports OAuth2 and API key authentication.
    """

    # Default API keys (hashed) - add your keys here
    DEFAULT_API_KEYS = set()

    def __init__(self):
        self._oauth_tokens: Dict[str, TokenData] = {}
        self._authorization_codes: Dict[str, Dict[str, Any]] = {}
        self._api_keys: set = set()
        self._oauth_password_hash: Optional[str] = None
        self._pending_authorizations: Dict[str, Dict[str, Any]] = {}  # pending_id -> auth params

        self._load_tokens()
        self._load_api_keys()
        self._load_oauth_password()

    def _load_tokens(self):
        """Load OAuth tokens from persistent storage."""
        if TOKEN_STORAGE_FILE.exists():
            try:
                with open(TOKEN_STORAGE_FILE, 'r') as f:
                    data = json.load(f)
                for token, token_data in data.get('tokens', {}).items():
                    self._oauth_tokens[token] = TokenData(
                        client_id=token_data['client_id'],
                        scope=token_data.get('scope', 'mcp'),
                        expires_at=datetime.fromisoformat(token_data['expires_at']),
                        created_at=datetime.fromisoformat(token_data['created_at'])
                    )
                logger.info(f"Loaded {len(self._oauth_tokens)} OAuth tokens")
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")

    def _save_tokens(self):
        """Save OAuth tokens to persistent storage."""
        try:
            serializable = {}
            for token, data in self._oauth_tokens.items():
                serializable[token] = {
                    'client_id': data.client_id,
                    'scope': data.scope,
                    'expires_at': data.expires_at.isoformat(),
                    'created_at': data.created_at.isoformat()
                }
            with open(TOKEN_STORAGE_FILE, 'w') as f:
                json.dump({'tokens': serializable}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def _load_api_keys(self):
        """Load API keys from storage."""
        self._api_keys = set(self.DEFAULT_API_KEYS)

        if API_KEYS_FILE.exists():
            try:
                with open(API_KEYS_FILE, 'r') as f:
                    data = json.load(f)
                self._api_keys.update(data.get('keys', []))
                logger.info(f"Loaded {len(self._api_keys)} API keys")
            except Exception as e:
                logger.error(f"Failed to load API keys: {e}")

    def _load_oauth_password(self):
        """Load OAuth password hash from storage."""
        if OAUTH_PASSWORD_FILE.exists():
            try:
                with open(OAUTH_PASSWORD_FILE, 'r') as f:
                    data = json.load(f)
                self._oauth_password_hash = data.get('password_hash')
                logger.info("OAuth password loaded")
            except Exception as e:
                logger.error(f"Failed to load OAuth password: {e}")

    def set_oauth_password(self, password: str) -> None:
        """Set the OAuth authorization password."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self._oauth_password_hash = password_hash
        try:
            with open(OAUTH_PASSWORD_FILE, 'w') as f:
                json.dump({'password_hash': password_hash}, f, indent=2)
            logger.info("OAuth password set")
        except Exception as e:
            logger.error(f"Failed to save OAuth password: {e}")

    def verify_oauth_password(self, password: str) -> bool:
        """Verify OAuth password. Returns True if no password is set."""
        if not self._oauth_password_hash:
            return True  # No password required if not set
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self._oauth_password_hash

    def requires_oauth_password(self) -> bool:
        """Check if OAuth password is required."""
        return self._oauth_password_hash is not None

    def create_pending_authorization(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str = "mcp",
        state: str = "",
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> str:
        """Create a pending authorization that requires password approval."""
        pending_id = secrets.token_urlsafe(16)
        self._pending_authorizations[pending_id] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        return pending_id

    def approve_pending_authorization(self, pending_id: str, password: str) -> Optional[str]:
        """
        Approve a pending authorization with password.

        Returns authorization code if successful, None if failed.
        """
        if pending_id not in self._pending_authorizations:
            return None

        pending = self._pending_authorizations[pending_id]

        # Check expiration
        if datetime.now() >= pending['expires_at']:
            del self._pending_authorizations[pending_id]
            return None

        # Verify password
        if not self.verify_oauth_password(password):
            return None

        # Create authorization code
        code = self.create_authorization_code(
            client_id=pending['client_id'],
            redirect_uri=pending['redirect_uri'],
            scope=pending['scope'],
            code_challenge=pending['code_challenge'],
            code_challenge_method=pending['code_challenge_method']
        )

        # Remove pending authorization
        del self._pending_authorizations[pending_id]

        return code

    def get_pending_authorization(self, pending_id: str) -> Optional[Dict[str, Any]]:
        """Get pending authorization details."""
        if pending_id not in self._pending_authorizations:
            return None
        pending = self._pending_authorizations[pending_id]
        if datetime.now() >= pending['expires_at']:
            del self._pending_authorizations[pending_id]
            return None
        return pending

    def add_api_key(self, key: str) -> str:
        """
        Add a new API key (stores hash).

        Args:
            key: Plain text API key

        Returns:
            The key hash (for reference)
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self._api_keys.add(key_hash)

        # Save to file
        try:
            with open(API_KEYS_FILE, 'w') as f:
                json.dump({'keys': list(self._api_keys)}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")

        return key_hash

    def generate_api_key(self) -> tuple[str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (plain_key, key_hash)
        """
        plain_key = f"mcp2_{secrets.token_urlsafe(32)}"
        key_hash = self.add_api_key(plain_key)
        return plain_key, key_hash

    def validate_api_key(self, key: str) -> bool:
        """Validate an API key."""
        if not self._api_keys:
            # No keys configured = open access (development mode)
            return True

        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key_hash in self._api_keys

    def validate_bearer_token(self, token: str) -> Optional[TokenData]:
        """
        Validate a Bearer token (OAuth access token).

        Returns:
            TokenData if valid, None otherwise
        """
        if token not in self._oauth_tokens:
            return None

        data = self._oauth_tokens[token]

        # Check expiration
        if datetime.now() >= data.expires_at:
            # Token expired
            del self._oauth_tokens[token]
            self._save_tokens()
            return None

        return data

    def authenticate(self, auth_header: Optional[str] = None, api_key_header: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Authenticate a request.

        Args:
            auth_header: Authorization header value
            api_key_header: X-API-Key header value

        Returns:
            Tuple of (is_authenticated, error_message)
        """
        # Check API key first
        if api_key_header:
            if self.validate_api_key(api_key_header):
                return True, None
            return False, "Invalid API key"

        # Check Bearer token
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                token_data = self.validate_bearer_token(token)
                if token_data:
                    return True, None
                return False, "Invalid or expired token"
            return False, "Invalid Authorization header format"

        # No auth provided - check if open access is allowed
        if not self._api_keys and not self._oauth_tokens:
            # Development mode - allow open access
            return True, None

        return False, "Authentication required"

    # OAuth2 flow methods

    def create_authorization_code(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str = "mcp",
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> str:
        """Create an authorization code."""
        code = secrets.token_urlsafe(32)

        self._authorization_codes[code] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=10)
        }

        logger.info(f"Created authorization code for client {client_id}")
        return code

    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Returns:
            Token response dict or None if invalid
        """
        if code not in self._authorization_codes:
            logger.warning(f"Invalid authorization code: {code[:20]}...")
            return None

        code_data = self._authorization_codes[code]

        # Validate code
        if code_data['client_id'] != client_id:
            logger.warning(f"Client ID mismatch: {client_id} vs {code_data['client_id']}")
            return None

        if code_data['redirect_uri'] != redirect_uri:
            logger.warning(f"Redirect URI mismatch")
            return None

        if datetime.now() >= code_data['expires_at']:
            logger.warning(f"Authorization code expired")
            del self._authorization_codes[code]
            return None

        # Verify PKCE if used
        if code_data.get('code_challenge'):
            if not code_verifier:
                logger.warning("Code verifier required but not provided")
                return None

            if code_data['code_challenge_method'] == 'S256':
                import base64
                verifier_hash = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                ).decode().rstrip('=')
                if verifier_hash != code_data['code_challenge']:
                    logger.warning("Code verifier mismatch")
                    return None
            elif code_data['code_challenge_method'] == 'plain':
                if code_verifier != code_data['code_challenge']:
                    logger.warning("Code verifier mismatch (plain)")
                    return None

        # Generate access token
        access_token = secrets.token_urlsafe(32)
        expires_in = 3600  # 1 hour

        self._oauth_tokens[access_token] = TokenData(
            client_id=client_id,
            scope=code_data.get('scope', 'mcp'),
            expires_at=datetime.now() + timedelta(seconds=expires_in),
            created_at=datetime.now()
        )
        self._save_tokens()

        # Remove used code
        del self._authorization_codes[code]

        logger.info(f"Generated access token for client {client_id}")

        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
            'scope': code_data.get('scope', 'mcp')
        }

    def create_client_credentials_token(self, client_id: str, scope: str = "mcp") -> Dict[str, Any]:
        """Create token via client credentials grant."""
        access_token = secrets.token_urlsafe(32)
        expires_in = 3600

        self._oauth_tokens[access_token] = TokenData(
            client_id=client_id,
            scope=scope,
            expires_at=datetime.now() + timedelta(seconds=expires_in),
            created_at=datetime.now()
        )
        self._save_tokens()

        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
            'scope': scope
        }

    def get_oauth_metadata(self, base_url: str) -> Dict[str, Any]:
        """Get OAuth2 authorization server metadata (RFC 8414)."""
        return {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "response_types_supported": ["code"],
            "code_challenge_methods_supported": ["S256", "plain"],
            "scopes_supported": ["mcp"],
        }


# Global auth manager instance
auth_manager = AuthManager()
