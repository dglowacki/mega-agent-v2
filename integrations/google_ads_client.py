"""
Google Ads API Client for mega-agent2.

Async wrapper around Google Ads API for campaign management and reporting.
Supports customer accounts, campaigns, and performance metrics.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional

try:
    from google.ads.googleads.client import GoogleAdsClient as GoogleAdsSDKClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False


class GoogleAdsClient:
    """Async client for Google Ads API operations."""

    def __init__(self):
        """Initialize Google Ads client from environment or config file."""
        if not GOOGLE_ADS_AVAILABLE:
            raise ImportError("Google Ads SDK not available. Install with: pip install google-ads")

        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Google Ads API client from credentials (synchronous)."""
        try:
            # Google Ads API credentials from environment or google-ads.yaml file
            self.client = GoogleAdsSDKClient.load_from_env()
        except Exception as e:
            raise Exception(f"Failed to initialize Google Ads client: {e}")

    # ============================================================================
    # Customer Accounts
    # ============================================================================

    async def list_accessible_customers(self) -> List[Dict[str, Any]]:
        """
        List all accessible customer accounts.

        Returns:
            List of customer accounts with IDs and resource names
        """
        def _list():
            try:
                customer_service = self.client.get_service("CustomerService")
                accessible_customers = customer_service.list_accessible_customers()

                customers = []
                for resource_name in accessible_customers.resource_names:
                    customer_id = resource_name.split('/')[-1]
                    customers.append({
                        "customer_id": customer_id,
                        "resource_name": resource_name
                    })

                return customers
            except GoogleAdsException as ex:
                raise Exception(f"Google Ads API error: {ex}")

        return await asyncio.to_thread(_list)

    async def get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """Get customer account information.

        Args:
            customer_id: Google Ads customer ID

        Returns:
            Customer information
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                query = """
                    SELECT
                        customer.id,
                        customer.descriptive_name,
                        customer.currency_code,
                        customer.time_zone,
                        customer.manager
                    FROM customer
                    LIMIT 1
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                for row in response:
                    customer = row.customer
                    return {
                        "id": customer.id,
                        "name": customer.descriptive_name,
                        "currency": customer.currency_code,
                        "timezone": customer.time_zone,
                        "is_manager": customer.manager
                    }

                return {}
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get customer info: {ex}")

        return await asyncio.to_thread(_get)

    # ============================================================================
    # Campaigns
    # ============================================================================

    async def get_campaigns(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all campaigns for a customer account.

        Args:
            customer_id: Google Ads customer ID

        Returns:
            List of campaigns with details
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                query = """
                    SELECT
                        campaign.id,
                        campaign.name,
                        campaign.status,
                        campaign.advertising_channel_type,
                        campaign.bidding_strategy_type,
                        campaign.start_date,
                        campaign.end_date
                    FROM campaign
                    ORDER BY campaign.id
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                campaigns = []
                for row in response:
                    campaign = row.campaign
                    campaigns.append({
                        "id": campaign.id,
                        "name": campaign.name,
                        "status": campaign.status.name,
                        "channel_type": campaign.advertising_channel_type.name,
                        "bidding_strategy": campaign.bidding_strategy_type.name,
                        "start_date": campaign.start_date,
                        "end_date": campaign.end_date if campaign.end_date else None
                    })

                return campaigns
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get campaigns: {ex}")

        return await asyncio.to_thread(_get)

    async def get_campaign(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """Get a specific campaign by ID.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                query = f"""
                    SELECT
                        campaign.id,
                        campaign.name,
                        campaign.status,
                        campaign.advertising_channel_type,
                        campaign.bidding_strategy_type,
                        campaign.start_date,
                        campaign.end_date,
                        campaign.budget
                    FROM campaign
                    WHERE campaign.id = {campaign_id}
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                for row in response:
                    campaign = row.campaign
                    return {
                        "id": campaign.id,
                        "name": campaign.name,
                        "status": campaign.status.name,
                        "channel_type": campaign.advertising_channel_type.name,
                        "bidding_strategy": campaign.bidding_strategy_type.name,
                        "start_date": campaign.start_date,
                        "end_date": campaign.end_date if campaign.end_date else None,
                        "budget": campaign.budget
                    }

                return {}
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get campaign: {ex}")

        return await asyncio.to_thread(_get)

    # ============================================================================
    # Performance Metrics
    # ============================================================================

    async def get_campaign_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get campaign performance metrics.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional specific campaign ID
            date_range: Number of days to look back (default 30)

        Returns:
            List of performance metrics by date
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

                query = f"""
                    SELECT
                        campaign.id,
                        campaign.name,
                        metrics.impressions,
                        metrics.clicks,
                        metrics.ctr,
                        metrics.average_cpc,
                        metrics.cost_micros,
                        metrics.conversions,
                        metrics.conversions_value,
                        metrics.cost_per_conversion,
                        segments.date
                    FROM campaign
                    WHERE segments.date DURING LAST_{date_range}_DAYS
                    {campaign_filter}
                    ORDER BY segments.date DESC
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                performance = []
                for row in response:
                    campaign = row.campaign
                    metrics = row.metrics
                    segments = row.segments

                    performance.append({
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "date": segments.date,
                        "impressions": metrics.impressions,
                        "clicks": metrics.clicks,
                        "ctr": metrics.ctr,
                        "average_cpc": metrics.average_cpc / 1_000_000,
                        "cost": metrics.cost_micros / 1_000_000,
                        "conversions": metrics.conversions,
                        "conversions_value": metrics.conversions_value,
                        "cost_per_conversion": metrics.cost_per_conversion / 1_000_000 if metrics.cost_per_conversion else 0
                    })

                return performance
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get campaign performance: {ex}")

        return await asyncio.to_thread(_get)

    async def get_account_summary(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get overall account performance summary.

        Args:
            customer_id: Google Ads customer ID
            days: Number of days to analyze (default 30)

        Returns:
            Summary metrics for the account
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                query = f"""
                    SELECT
                        metrics.impressions,
                        metrics.clicks,
                        metrics.ctr,
                        metrics.average_cpc,
                        metrics.cost_micros,
                        metrics.conversions,
                        metrics.conversions_value,
                        metrics.cost_per_conversion
                    FROM customer
                    WHERE segments.date DURING LAST_{days}_DAYS
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                total_impressions = 0
                total_clicks = 0
                total_cost_micros = 0
                total_conversions = 0
                total_conversions_value = 0

                for row in response:
                    metrics = row.metrics
                    total_impressions += metrics.impressions
                    total_clicks += metrics.clicks
                    total_cost_micros += metrics.cost_micros
                    total_conversions += metrics.conversions
                    total_conversions_value += metrics.conversions_value

                ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                avg_cpc = (total_cost_micros / total_clicks) if total_clicks > 0 else 0
                cost_per_conversion = (total_cost_micros / total_conversions) if total_conversions > 0 else 0

                return {
                    "period_days": days,
                    "impressions": total_impressions,
                    "clicks": total_clicks,
                    "ctr": round(ctr, 2),
                    "average_cpc": round(avg_cpc / 1_000_000, 2),
                    "total_cost": round(total_cost_micros / 1_000_000, 2),
                    "conversions": total_conversions,
                    "conversions_value": round(total_conversions_value, 2),
                    "cost_per_conversion": round(cost_per_conversion / 1_000_000, 2),
                    "roas": round(total_conversions_value / (total_cost_micros / 1_000_000), 2) if total_cost_micros > 0 else 0
                }
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get account summary: {ex}")

        return await asyncio.to_thread(_get)

    # ============================================================================
    # Campaign Management
    # ============================================================================

    async def pause_campaign(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """Pause a campaign.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID

        Returns:
            Operation result
        """
        def _pause():
            try:
                campaign_service = self.client.get_service("CampaignService")
                campaign_operation = self.client.get_type("CampaignOperation")
                campaign = campaign_operation.update
                campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
                campaign.status = self.client.enums.CampaignStatusEnum.PAUSED

                self.client.copy_from(
                    campaign_operation.update_mask,
                    self.client.get_type("FieldMask", version="v16")(paths=["status"])
                )

                response = campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation]
                )

                return {
                    "status": "success",
                    "resource_name": response.results[0].resource_name,
                    "new_status": "PAUSED"
                }
            except GoogleAdsException as ex:
                raise Exception(f"Failed to pause campaign: {ex}")

        return await asyncio.to_thread(_pause)

    async def enable_campaign(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """Enable a paused campaign.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID

        Returns:
            Operation result
        """
        def _enable():
            try:
                campaign_service = self.client.get_service("CampaignService")
                campaign_operation = self.client.get_type("CampaignOperation")
                campaign = campaign_operation.update
                campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
                campaign.status = self.client.enums.CampaignStatusEnum.ENABLED

                self.client.copy_from(
                    campaign_operation.update_mask,
                    self.client.get_type("FieldMask", version="v16")(paths=["status"])
                )

                response = campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation]
                )

                return {
                    "status": "success",
                    "resource_name": response.results[0].resource_name,
                    "new_status": "ENABLED"
                }
            except GoogleAdsException as ex:
                raise Exception(f"Failed to enable campaign: {ex}")

        return await asyncio.to_thread(_enable)

    # ============================================================================
    # Ad Groups
    # ============================================================================

    async def get_ad_groups(self, customer_id: str, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ad groups for campaigns.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID filter

        Returns:
            List of ad groups
        """
        def _get():
            try:
                ga_service = self.client.get_service("GoogleAdsService")

                campaign_filter = f"WHERE ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'" if campaign_id else ""

                query = f"""
                    SELECT
                        ad_group.id,
                        ad_group.name,
                        ad_group.status,
                        ad_group.type,
                        campaign.id,
                        campaign.name
                    FROM ad_group
                    {campaign_filter}
                    ORDER BY ad_group.id
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                ad_groups = []
                for row in response:
                    ad_group = row.ad_group
                    campaign = row.campaign

                    ad_groups.append({
                        "id": ad_group.id,
                        "name": ad_group.name,
                        "status": ad_group.status.name,
                        "type": ad_group.type_.name,
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name
                    })

                return ad_groups
            except GoogleAdsException as ex:
                raise Exception(f"Failed to get ad groups: {ex}")

        return await asyncio.to_thread(_get)
