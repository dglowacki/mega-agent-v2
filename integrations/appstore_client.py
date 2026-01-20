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
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/apps",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
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

    # ============================================================================
    # TestFlight - Builds
    # ============================================================================

    async def list_builds(
        self,
        app_id: Optional[str] = None,
        version: Optional[str] = None,
        processing_state: Optional[str] = None,
        beta_review_state: Optional[str] = None,
        limit: int = 10,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """List TestFlight builds.

        Args:
            app_id: Filter by app ID
            version: Filter by version string
            processing_state: Filter by processing state (PROCESSING, FAILED, INVALID, VALID)
            beta_review_state: Filter by beta review state
            limit: Maximum number of builds to return
            account: Account name

        Returns:
            Dict with builds list
        """
        try:
            params = {
                "sort": "-uploadedDate",
                "limit": str(limit),
                "include": "preReleaseVersion,betaAppReviewSubmission"
            }

            if app_id:
                params["filter[app]"] = app_id
            if version:
                params["filter[version]"] = version
            if processing_state:
                params["filter[processingState]"] = processing_state

            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/builds",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            builds = data.get("data", [])
            included = data.get("included", [])

            # Create lookup for included objects
            included_lookup = {}
            for item in included:
                key = f"{item['type']}:{item['id']}"
                included_lookup[key] = item

            formatted_builds = []
            for build in builds:
                attrs = build.get("attributes", {})
                relationships = build.get("relationships", {})

                # Get pre-release version
                pre_release_rel = relationships.get("preReleaseVersion", {}).get("data")
                pre_release_version = None
                if pre_release_rel:
                    key = f"{pre_release_rel['type']}:{pre_release_rel['id']}"
                    pre_release_obj = included_lookup.get(key, {})
                    pre_release_version = pre_release_obj.get("attributes", {}).get("version")

                # Get beta review status
                review_rel = relationships.get("betaAppReviewSubmission", {}).get("data")
                review_state = None
                if review_rel:
                    key = f"{review_rel['type']}:{review_rel['id']}"
                    review_obj = included_lookup.get(key, {})
                    review_state = review_obj.get("attributes", {}).get("betaReviewState")

                formatted_builds.append({
                    "id": build["id"],
                    "version": pre_release_version,
                    "build_number": attrs.get("version"),
                    "uploaded_date": attrs.get("uploadedDate"),
                    "processing_state": attrs.get("processingState"),
                    "beta_review_state": review_state,
                    "min_os_version": attrs.get("minOsVersion"),
                    "uses_non_exempt_encryption": attrs.get("usesNonExemptEncryption")
                })

            return {
                "type": "testflight_builds",
                "account": account,
                "count": len(formatted_builds),
                "builds": formatted_builds,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def get_build(
        self,
        build_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Get details for a specific build.

        Args:
            build_id: Build ID
            account: Account name

        Returns:
            Dict with build details
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            params = {"include": "preReleaseVersion,betaAppReviewSubmission,app"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/builds/{build_id}",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            build = data.get("data", {})
            included = data.get("included", [])
            attrs = build.get("attributes", {})
            relationships = build.get("relationships", {})

            # Create lookup
            included_lookup = {}
            for item in included:
                key = f"{item['type']}:{item['id']}"
                included_lookup[key] = item

            # Get app info
            app_rel = relationships.get("app", {}).get("data")
            app_name = None
            if app_rel:
                key = f"{app_rel['type']}:{app_rel['id']}"
                app_obj = included_lookup.get(key, {})
                app_name = app_obj.get("attributes", {}).get("name")

            # Get version
            pre_release_rel = relationships.get("preReleaseVersion", {}).get("data")
            version = None
            if pre_release_rel:
                key = f"{pre_release_rel['type']}:{pre_release_rel['id']}"
                pre_release_obj = included_lookup.get(key, {})
                version = pre_release_obj.get("attributes", {}).get("version")

            # Get review status
            review_rel = relationships.get("betaAppReviewSubmission", {}).get("data")
            review_state = None
            submitted_date = None
            if review_rel:
                key = f"{review_rel['type']}:{review_rel['id']}"
                review_obj = included_lookup.get(key, {})
                review_state = review_obj.get("attributes", {}).get("betaReviewState")
                submitted_date = review_obj.get("attributes", {}).get("submittedDate")

            return {
                "type": "testflight_build",
                "account": account,
                "build": {
                    "id": build["id"],
                    "app_name": app_name,
                    "version": version,
                    "build_number": attrs.get("version"),
                    "uploaded_date": attrs.get("uploadedDate"),
                    "expiration_date": attrs.get("expirationDate"),
                    "processing_state": attrs.get("processingState"),
                    "beta_review_state": review_state,
                    "beta_review_submitted": submitted_date,
                    "min_os_version": attrs.get("minOsVersion"),
                    "icon_asset_token": attrs.get("iconAssetToken"),
                    "uses_non_exempt_encryption": attrs.get("usesNonExemptEncryption")
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # TestFlight - Beta Review
    # ============================================================================

    async def submit_for_beta_review(
        self,
        build_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Submit a build for TestFlight beta review.

        Args:
            build_id: Build ID to submit
            account: Account name

        Returns:
            Dict with submission result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "data": {
                    "type": "betaAppReviewSubmissions",
                    "relationships": {
                        "build": {
                            "data": {
                                "type": "builds",
                                "id": build_id
                            }
                        }
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/betaAppReviewSubmissions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            submission = data.get("data", {})
            attrs = submission.get("attributes", {})

            return {
                "type": "testflight_submission",
                "account": account,
                "submission_id": submission.get("id"),
                "build_id": build_id,
                "beta_review_state": attrs.get("betaReviewState"),
                "submitted_date": attrs.get("submittedDate"),
                "status": "success"
            }
        except aiohttp.ClientResponseError as e:
            error_msg = str(e)
            if e.status == 409:
                error_msg = "Build already submitted for review or has an existing submission"
            return {
                "type": "appstore_error",
                "error": error_msg,
                "status": "failed"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def get_beta_review_status(
        self,
        build_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Get beta review status for a build.

        Args:
            build_id: Build ID
            account: Account name

        Returns:
            Dict with review status
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/builds/{build_id}/betaAppReviewSubmission",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    if response.status == 404:
                        return {
                            "type": "testflight_review_status",
                            "account": account,
                            "build_id": build_id,
                            "submitted": False,
                            "beta_review_state": None,
                            "status": "success"
                        }
                    response.raise_for_status()
                    data = await response.json()

            submission = data.get("data", {})
            attrs = submission.get("attributes", {})

            return {
                "type": "testflight_review_status",
                "account": account,
                "build_id": build_id,
                "submission_id": submission.get("id"),
                "submitted": True,
                "beta_review_state": attrs.get("betaReviewState"),
                "submitted_date": attrs.get("submittedDate"),
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # TestFlight - Beta Testers
    # ============================================================================

    async def list_beta_testers(
        self,
        app_id: Optional[str] = None,
        email: Optional[str] = None,
        beta_group_id: Optional[str] = None,
        limit: int = 50,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """List beta testers.

        Args:
            app_id: Filter by app ID
            email: Filter by email address
            beta_group_id: Filter by beta group ID
            limit: Maximum number of testers to return
            account: Account name

        Returns:
            Dict with testers list
        """
        try:
            params = {
                "limit": str(limit),
                "sort": "email"
            }

            if email:
                params["filter[email]"] = email
            if app_id:
                params["filter[apps]"] = app_id
            if beta_group_id:
                params["filter[betaGroups]"] = beta_group_id

            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/betaTesters",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            testers = data.get("data", [])

            formatted_testers = []
            for tester in testers:
                attrs = tester.get("attributes", {})
                formatted_testers.append({
                    "id": tester["id"],
                    "email": attrs.get("email"),
                    "first_name": attrs.get("firstName"),
                    "last_name": attrs.get("lastName"),
                    "invite_type": attrs.get("inviteType"),
                    "state": attrs.get("state")
                })

            return {
                "type": "testflight_testers",
                "account": account,
                "count": len(formatted_testers),
                "testers": formatted_testers,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def add_beta_tester(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        beta_group_ids: Optional[List[str]] = None,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Add a new beta tester.

        Args:
            email: Tester's email address
            first_name: Tester's first name
            last_name: Tester's last name
            beta_group_ids: List of beta group IDs to add tester to
            account: Account name

        Returns:
            Dict with created tester info
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            attributes = {"email": email}
            if first_name:
                attributes["firstName"] = first_name
            if last_name:
                attributes["lastName"] = last_name

            payload = {
                "data": {
                    "type": "betaTesters",
                    "attributes": attributes
                }
            }

            if beta_group_ids:
                payload["data"]["relationships"] = {
                    "betaGroups": {
                        "data": [{"type": "betaGroups", "id": gid} for gid in beta_group_ids]
                    }
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/betaTesters",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            tester = data.get("data", {})
            attrs = tester.get("attributes", {})

            return {
                "type": "testflight_tester_created",
                "account": account,
                "tester": {
                    "id": tester.get("id"),
                    "email": attrs.get("email"),
                    "first_name": attrs.get("firstName"),
                    "last_name": attrs.get("lastName"),
                    "invite_type": attrs.get("inviteType"),
                    "state": attrs.get("state")
                },
                "status": "success"
            }
        except aiohttp.ClientResponseError as e:
            error_msg = str(e)
            if e.status == 409:
                error_msg = "Beta tester with this email already exists"
            return {
                "type": "appstore_error",
                "error": error_msg,
                "status": "failed"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def remove_beta_tester(
        self,
        tester_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Remove a beta tester.

        Args:
            tester_id: Beta tester ID to remove
            account: Account name

        Returns:
            Dict with deletion result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/betaTesters/{tester_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()

            return {
                "type": "testflight_tester_removed",
                "account": account,
                "tester_id": tester_id,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    # ============================================================================
    # TestFlight - Beta Groups
    # ============================================================================

    async def list_beta_groups(
        self,
        app_id: Optional[str] = None,
        name: Optional[str] = None,
        is_internal: Optional[bool] = None,
        limit: int = 50,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """List beta groups.

        Args:
            app_id: Filter by app ID
            name: Filter by group name
            is_internal: Filter by internal/external status
            limit: Maximum number of groups to return
            account: Account name

        Returns:
            Dict with beta groups list
        """
        try:
            params = {
                "limit": str(limit),
                "sort": "name"
            }

            if app_id:
                params["filter[app]"] = app_id
            if name:
                params["filter[name]"] = name
            if is_internal is not None:
                params["filter[isInternalGroup]"] = str(is_internal).lower()

            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/betaGroups",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            groups = data.get("data", [])

            formatted_groups = []
            for group in groups:
                attrs = group.get("attributes", {})
                formatted_groups.append({
                    "id": group["id"],
                    "name": attrs.get("name"),
                    "is_internal": attrs.get("isInternalGroup"),
                    "public_link_enabled": attrs.get("publicLinkEnabled"),
                    "public_link": attrs.get("publicLink"),
                    "public_link_limit": attrs.get("publicLinkLimit"),
                    "public_link_limit_enabled": attrs.get("publicLinkLimitEnabled"),
                    "created_date": attrs.get("createdDate")
                })

            return {
                "type": "testflight_groups",
                "account": account,
                "count": len(formatted_groups),
                "groups": formatted_groups,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def create_beta_group(
        self,
        app_id: str,
        name: str,
        is_internal: bool = False,
        public_link_enabled: bool = False,
        public_link_limit: Optional[int] = None,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Create a new beta group.

        Args:
            app_id: App ID to create group for
            name: Group name
            is_internal: Whether this is an internal group
            public_link_enabled: Whether to enable public link
            public_link_limit: Maximum testers via public link
            account: Account name

        Returns:
            Dict with created group info
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            attributes = {
                "name": name,
                "isInternalGroup": is_internal,
                "publicLinkEnabled": public_link_enabled
            }

            if public_link_limit is not None:
                attributes["publicLinkLimit"] = public_link_limit
                attributes["publicLinkLimitEnabled"] = True

            payload = {
                "data": {
                    "type": "betaGroups",
                    "attributes": attributes,
                    "relationships": {
                        "app": {
                            "data": {
                                "type": "apps",
                                "id": app_id
                            }
                        }
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/betaGroups",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            group = data.get("data", {})
            attrs = group.get("attributes", {})

            return {
                "type": "testflight_group_created",
                "account": account,
                "group": {
                    "id": group.get("id"),
                    "name": attrs.get("name"),
                    "is_internal": attrs.get("isInternalGroup"),
                    "public_link_enabled": attrs.get("publicLinkEnabled"),
                    "public_link": attrs.get("publicLink")
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def delete_beta_group(
        self,
        group_id: str,
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Delete a beta group.

        Args:
            group_id: Beta group ID to delete
            account: Account name

        Returns:
            Dict with deletion result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/betaGroups/{group_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()

            return {
                "type": "testflight_group_deleted",
                "account": account,
                "group_id": group_id,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def add_build_to_group(
        self,
        group_id: str,
        build_ids: List[str],
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Add builds to a beta group.

        Args:
            group_id: Beta group ID
            build_ids: List of build IDs to add
            account: Account name

        Returns:
            Dict with result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "data": [{"type": "builds", "id": bid} for bid in build_ids]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/betaGroups/{group_id}/relationships/builds",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()

            return {
                "type": "testflight_builds_added",
                "account": account,
                "group_id": group_id,
                "build_ids": build_ids,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def add_testers_to_group(
        self,
        group_id: str,
        tester_ids: List[str],
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Add testers to a beta group.

        Args:
            group_id: Beta group ID
            tester_ids: List of tester IDs to add
            account: Account name

        Returns:
            Dict with result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "data": [{"type": "betaTesters", "id": tid} for tid in tester_ids]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/betaGroups/{group_id}/relationships/betaTesters",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()

            return {
                "type": "testflight_testers_added",
                "account": account,
                "group_id": group_id,
                "tester_ids": tester_ids,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }

    async def remove_testers_from_group(
        self,
        group_id: str,
        tester_ids: List[str],
        account: str = "primary"
    ) -> Dict[str, Any]:
        """Remove testers from a beta group.

        Args:
            group_id: Beta group ID
            tester_ids: List of tester IDs to remove
            account: Account name

        Returns:
            Dict with result
        """
        try:
            token = self._generate_jwt(account)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "data": [{"type": "betaTesters", "id": tid} for tid in tester_ids]
            }

            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/betaGroups/{group_id}/relationships/betaTesters",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response.raise_for_status()

            return {
                "type": "testflight_testers_removed",
                "account": account,
                "group_id": group_id,
                "tester_ids": tester_ids,
                "status": "success"
            }
        except Exception as e:
            return {
                "type": "appstore_error",
                "error": str(e),
                "status": "failed"
            }
