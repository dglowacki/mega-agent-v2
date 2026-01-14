"""
App Store Connect API Client for mega-agent2.

Async client for interacting with Apple's App Store Connect API.
Supports multiple accounts, sales reports, analytics, and ASO management.
"""

import os
import time
import gzip
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
import aiohttp
import asyncio


class AppStoreConnectClient:
    """Async client for App Store Connect API."""

    def __init__(self):
        """Initialize App Store Connect client with multi-account support."""
        self.base_url = "https://api.appstoreconnect.apple.com/v1"
        self.accounts = self._load_accounts()
        self.vendor_number = os.getenv("APPSTORE_VENDOR_NUMBER", "")

    def _load_accounts(self) -> Dict[str, Dict[str, str]]:
        """Load App Store Connect accounts from environment variables.

        Returns:
            Dict mapping account names to credentials
        """
        accounts = {}

        # Load primary account
        if os.getenv("APPSTORE_KEY_ID"):
            accounts["primary"] = {
                "key_id": os.getenv("APPSTORE_KEY_ID"),
                "issuer_id": os.getenv("APPSTORE_ISSUER_ID"),
                "key_path": os.getenv("APPSTORE_KEY_PATH")
            }

        # Load additional accounts (APPSTORE_KEY_ID_2, etc.)
        i = 2
        while os.getenv(f"APPSTORE_KEY_ID_{i}"):
            accounts[f"account_{i}"] = {
                "key_id": os.getenv(f"APPSTORE_KEY_ID_{i}"),
                "issuer_id": os.getenv(f"APPSTORE_ISSUER_ID_{i}"),
                "key_path": os.getenv(f"APPSTORE_KEY_PATH_{i}")
            }
            i += 1

        return accounts

    def _generate_jwt(self, account: str = "primary") -> str:
        """Generate JWT token for App Store Connect API.

        Args:
            account: Account name (default: "primary")

        Returns:
            JWT token string

        Raises:
            ValueError: If account not configured
        """
        if account not in self.accounts:
            raise ValueError(f"Account '{account}' not configured")

        creds = self.accounts[account]

        # Read private key
        with open(creds["key_path"], 'r') as key_file:
            private_key = key_file.read()

        # Create JWT token
        headers = {
            "alg": "ES256",
            "kid": creds["key_id"],
            "typ": "JWT"
        }

        payload = {
            "iss": creds["issuer_id"],
            "iat": int(time.time()),
            "exp": int(time.time()) + 1200,  # 20 minutes
            "aud": "appstoreconnect-v1"
        }

        token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
        return token

    async def _request(
        self,
        method: str,
        endpoint: str,
        account: str = "primary",
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 90
    ) -> aiohttp.ClientResponse:
        """Make authenticated request to App Store Connect API.

        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint (relative to base_url)
            account: Account name
            params: Query parameters
            json_data: JSON request body
            timeout: Request timeout in seconds

        Returns:
            aiohttp ClientResponse

        Raises:
            aiohttp.ClientError: On request failure
        """
        token = self._generate_jwt(account)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith("http") else endpoint

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return response

    # ============================================================================
    # App Management
    # ============================================================================

    async def list_apps(self, account: str = "primary") -> Dict[str, Any]:
        """List all apps for the account.

        Args:
            account: Account name

        Returns:
            Dict with status, count, and list of apps
        """
        try:
            response = await self._request("GET", "apps", account=account)
            data = await response.json()
            apps = data.get("data", [])

            return {
                "type": "appstore_apps",
                "account": account,
                "count": len(apps),
                "apps": [
                    {
                        "id": app["id"],
                        "name": app["attributes"].get("name"),
                        "bundle_id": app["attributes"].get("bundleId"),
                        "sku": app["attributes"].get("sku")
                    }
                    for app in apps
                ],
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # Sales Reports
    # ============================================================================

    async def get_sales_report(
        self,
        account: str = "primary",
        frequency: str = "DAILY",
        report_type: str = "SALES",
        report_subtype: str = "SUMMARY",
        report_date: Optional[str] = None,
        vendor_number: Optional[str] = None,
        version: str = "1_0"
    ) -> Dict[str, Any]:
        """Get sales reports from App Store Connect.

        Args:
            account: Account name
            frequency: Report frequency (DAILY, WEEKLY, MONTHLY, YEARLY)
            report_type: Report type (SALES, PRE_ORDER, NEWSSTAND, SUBSCRIPTION, etc.)
            report_subtype: Report subtype (SUMMARY, DETAILED, etc.)
            report_date: Report date (YYYY-MM-DD), defaults to yesterday
            vendor_number: Vendor number, uses env var if not provided
            version: Report version (default: 1_0)

        Returns:
            Dict with parsed sales data
        """
        try:
            # Default to yesterday if no date provided
            if not report_date and frequency == "DAILY":
                report_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

            # Use configured vendor number if not provided
            if not vendor_number:
                vendor_number = self.vendor_number
                if not vendor_number:
                    raise ValueError("App Store vendor number is required")

            params = {
                "filter[frequency]": frequency,
                "filter[reportType]": report_type,
                "filter[vendorNumber]": vendor_number,
                "filter[version]": version
            }

            if report_subtype:
                params["filter[reportSubType]"] = report_subtype
            if report_date:
                params["filter[reportDate]"] = report_date

            response = await self._request("GET", "salesReports", account=account, params=params)

            # Sales reports are returned as gzipped TSV
            compressed_data = await response.read()
            decompressed = gzip.decompress(compressed_data)
            tsv_data = decompressed.decode('utf-8')

            # Parse TSV into list of dicts
            reader = csv.DictReader(tsv_data.splitlines(), delimiter='\t')
            rows = list(reader)

            return {
                "type": "appstore_sales",
                "account": account,
                "frequency": frequency,
                "report_type": report_type,
                "report_date": report_date,
                "row_count": len(rows),
                "data": rows,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # App Analytics
    # ============================================================================

    async def get_app_analytics(
        self,
        app_id: str,
        account: str = "primary",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get app analytics data.

        Args:
            app_id: App ID
            account: Account name
            metrics: List of metrics to retrieve

        Returns:
            Dict with analytics data
        """
        try:
            # Default metrics if none provided
            if not metrics:
                metrics = ["downloads", "sessions", "activeDevices"]

            response = await self._request(
                "GET",
                f"apps/{app_id}/perfPowerMetrics",
                account=account
            )
            data = await response.json()

            return {
                "type": "appstore_analytics",
                "account": account,
                "app_id": app_id,
                "data": data.get("data", []),
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # App Availability (ASO - Countries/Territories)
    # ============================================================================

    async def get_availability(
        self,
        app_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Get app availability (countries/territories).

        Args:
            app_id: App ID
            account: Account name

        Returns:
            Dict with availability data
        """
        try:
            response = await self._request(
                "GET",
                f"apps/{app_id}/appAvailability",
                account=account
            )
            data = await response.json()

            availability_data = data.get("data", {})
            relationships = availability_data.get("relationships", {})
            territories = relationships.get("availableTerritories", {}).get("data", [])

            return {
                "type": "appstore_availability",
                "account": account,
                "app_id": app_id,
                "available_in_new_territories": availability_data.get("attributes", {}).get("availableInNewTerritories"),
                "territory_count": len(territories),
                "territories": [t.get("id") for t in territories],
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def update_availability(
        self,
        app_id: str,
        available_in_new_territories: bool,
        territory_ids: Optional[List[str]] = None,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Update app availability.

        Args:
            app_id: App ID
            available_in_new_territories: Whether to auto-enable in new territories
            territory_ids: List of territory IDs to make app available in
            account: Account name

        Returns:
            Dict with update result
        """
        try:
            # First get current availability ID
            availability_response = await self.get_availability(app_id, account)
            if availability_response["status"] != "success":
                return availability_response

            # Build update payload
            update_data = {
                "data": {
                    "type": "appAvailabilities",
                    "id": app_id,
                    "attributes": {
                        "availableInNewTerritories": available_in_new_territories
                    }
                }
            }

            if territory_ids:
                update_data["data"]["relationships"] = {
                    "availableTerritories": {
                        "data": [{"type": "territories", "id": tid} for tid in territory_ids]
                    }
                }

            response = await self._request(
                "PATCH",
                f"apps/{app_id}/appAvailability",
                account=account,
                json_data=update_data
            )
            data = await response.json()

            return {
                "type": "appstore_availability_update",
                "account": account,
                "app_id": app_id,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def list_territories(self, account: str = "primary") -> Dict[str, Any]:
        """List all available territories.

        Args:
            account: Account name

        Returns:
            Dict with list of territories
        """
        try:
            response = await self._request("GET", "territories", account=account)
            data = await response.json()
            territories = data.get("data", [])

            return {
                "type": "appstore_territories",
                "account": account,
                "count": len(territories),
                "territories": [
                    {
                        "id": t["id"],
                        "currency": t["attributes"].get("currency")
                    }
                    for t in territories
                ],
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # ASO - Keywords
    # ============================================================================

    async def get_keywords(
        self,
        app_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Get app keywords (ASO).

        Args:
            app_id: App ID
            account: Account name

        Returns:
            Dict with keyword data
        """
        try:
            # Get app store versions
            response = await self._request(
                "GET",
                f"apps/{app_id}/appStoreVersions",
                account=account,
                params={"filter[platform]": "IOS", "filter[appStoreState]": "READY_FOR_SALE"}
            )
            data = await response.json()
            versions = data.get("data", [])

            if not versions:
                return {
                    "type": "appstore_keywords",
                    "account": account,
                    "app_id": app_id,
                    "keywords": {},
                    "status": "success",
                    "message": "No published versions found"
                }

            version_id = versions[0]["id"]

            # Get localizations for this version
            loc_response = await self._request(
                "GET",
                f"appStoreVersions/{version_id}/appStoreVersionLocalizations",
                account=account
            )
            loc_data = await loc_response.json()
            localizations = loc_data.get("data", [])

            keywords = {}
            for loc in localizations:
                locale = loc["attributes"].get("locale")
                keyword_text = loc["attributes"].get("keywords", "")
                keywords[locale] = keyword_text

            return {
                "type": "appstore_keywords",
                "account": account,
                "app_id": app_id,
                "version_id": version_id,
                "keywords": keywords,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def update_keywords(
        self,
        app_id: str,
        keywords: Dict[str, str],
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Update app keywords (ASO).

        Args:
            app_id: App ID
            keywords: Dict mapping locale to keyword string (e.g., {"en-US": "game, puzzle, fun"})
            account: Account name

        Returns:
            Dict with update result
        """
        try:
            # Get current version
            version_response = await self._request(
                "GET",
                f"apps/{app_id}/appStoreVersions",
                account=account,
                params={"filter[platform]": "IOS", "filter[appStoreState]": "READY_FOR_SALE"}
            )
            version_data = await version_response.json()
            versions = version_data.get("data", [])

            if not versions:
                return {
                    "type": "appstore_error",
                    "error": "No published version found",
                    "status": "failed"
                }

            version_id = versions[0]["id"]

            # Get localizations
            loc_response = await self._request(
                "GET",
                f"appStoreVersions/{version_id}/appStoreVersionLocalizations",
                account=account
            )
            loc_data = await loc_response.json()
            localizations = loc_data.get("data", [])

            # Update each localization
            updated_count = 0
            for loc in localizations:
                locale = loc["attributes"].get("locale")
                if locale in keywords:
                    loc_id = loc["id"]
                    update_data = {
                        "data": {
                            "type": "appStoreVersionLocalizations",
                            "id": loc_id,
                            "attributes": {
                                "keywords": keywords[locale]
                            }
                        }
                    }

                    await self._request(
                        "PATCH",
                        f"appStoreVersionLocalizations/{loc_id}",
                        account=account,
                        json_data=update_data
                    )
                    updated_count += 1

            return {
                "type": "appstore_keywords_update",
                "account": account,
                "app_id": app_id,
                "version_id": version_id,
                "updated_count": updated_count,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }
