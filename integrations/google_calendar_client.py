"""
Google Calendar API Client for mega-agent2.

Async wrapper around Google Calendar API.
Uses service account with domain-wide delegation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarClient:
    """Async client for Google Calendar API operations."""

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, credential_file: str = 'google-credentials-aquarius.json', user_email: Optional[str] = None):
        """
        Initialize Calendar client.

        Args:
            credential_file: Path to service account credentials
            user_email: Email to impersonate (requires domain-wide delegation)
        """
        credentials = service_account.Credentials.from_service_account_file(
            credential_file,
            scopes=self.SCOPES
        )

        if user_email:
            credentials = credentials.with_subject(user_email)

        self.service = build('calendar', 'v3', credentials=credentials)
        self.user_email = user_email

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars.

        Returns:
            List of calendar objects
        """
        def _list():
            try:
                calendar_list = self.service.calendarList().list().execute()
                return calendar_list.get('items', [])
            except HttpError as e:
                raise Exception(f"Error listing calendars: {e}")

        return await asyncio.to_thread(_list)

    async def list_events(
        self,
        calendar_id: str = 'primary',
        max_results: int = 10,
        days_ahead: int = 7,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List upcoming events.

        Args:
            calendar_id: Calendar ID (default: 'primary')
            max_results: Maximum events to return
            days_ahead: Number of days ahead to fetch events (if time_min/time_max not provided)
            time_min: RFC3339 timestamp for earliest event (overrides days_ahead)
            time_max: RFC3339 timestamp for latest event (overrides days_ahead)

        Returns:
            List of event objects
        """
        def _list():
            try:
                # Use provided times or calculate from days_ahead
                if not time_min:
                    now = datetime.utcnow().isoformat() + 'Z'
                else:
                    now = time_min

                if not time_max:
                    end_time = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
                else:
                    end_time = time_max

                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=now,
                    timeMax=end_time,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()

                return events_result.get('items', [])
            except HttpError as e:
                raise Exception(f"Error listing events: {e}")

        return await asyncio.to_thread(_list)

    async def get_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Get a specific event by ID.

        Args:
            event_id: Event ID
            calendar_id: Calendar ID

        Returns:
            Event object
        """
        def _get():
            try:
                return self.service.events().get(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
            except HttpError as e:
                raise Exception(f"Error getting event: {e}")

        return await asyncio.to_thread(_get)

    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = '',
        calendar_id: str = 'primary',
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
        timezone: str = 'America/Los_Angeles'
    ) -> Dict[str, Any]:
        """
        Create a calendar event.

        Args:
            summary: Event title
            start_time: Start datetime (ISO format string or datetime object)
            end_time: End datetime (ISO format string or datetime object)
            description: Event description
            calendar_id: Calendar ID
            attendees: List of attendee emails
            location: Event location
            timezone: Timezone name (default: America/Los_Angeles)

        Returns:
            Created event object
        """
        def _create():
            try:
                # Convert datetime objects to ISO format if needed
                if isinstance(start_time, datetime):
                    start_iso = start_time.isoformat()
                else:
                    start_iso = start_time

                if isinstance(end_time, datetime):
                    end_iso = end_time.isoformat()
                else:
                    end_iso = end_time

                event = {
                    'summary': summary,
                    'description': description,
                    'start': {
                        'dateTime': start_iso,
                        'timeZone': timezone,
                    },
                    'end': {
                        'dateTime': end_iso,
                        'timeZone': timezone,
                    },
                }

                if location:
                    event['location'] = location

                if attendees:
                    event['attendees'] = [{'email': email} for email in attendees]

                event_result = self.service.events().insert(
                    calendarId=calendar_id,
                    body=event
                ).execute()

                return event_result
            except HttpError as e:
                raise Exception(f"Error creating event: {e}")

        return await asyncio.to_thread(_create)

    async def update_event(
        self,
        event_id: str,
        calendar_id: str = 'primary',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing event.

        Args:
            event_id: Event ID to update
            calendar_id: Calendar ID
            **kwargs: Fields to update (summary, start, end, description, etc.)

        Returns:
            Updated event object
        """
        def _update():
            try:
                # Get existing event
                event = self.service.events().get(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()

                # Update fields
                for key, value in kwargs.items():
                    event[key] = value

                updated_event = self.service.events().update(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=event
                ).execute()

                return updated_event
            except HttpError as e:
                raise Exception(f"Error updating event: {e}")

        return await asyncio.to_thread(_update)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> bool:
        """Delete an event.

        Args:
            event_id: Event ID
            calendar_id: Calendar ID

        Returns:
            True if successful
        """
        def _delete():
            try:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
                return True
            except HttpError as e:
                raise Exception(f"Error deleting event: {e}")

        return await asyncio.to_thread(_delete)

    async def find_free_time(
        self,
        start_time: str,
        end_time: str,
        calendar_ids: Optional[List[str]] = None,
        duration_minutes: int = 30
    ) -> List[Dict[str, str]]:
        """
        Find free time slots in calendars.

        Args:
            start_time: Start of search window (ISO format)
            end_time: End of search window (ISO format)
            calendar_ids: List of calendar IDs to check (default: ['primary'])
            duration_minutes: Required slot duration in minutes

        Returns:
            List of free time slots with 'start' and 'end' times
        """
        def _find():
            try:
                if not calendar_ids:
                    calendar_ids_to_check = ['primary']
                else:
                    calendar_ids_to_check = calendar_ids

                # Query freebusy for all calendars
                body = {
                    "timeMin": start_time,
                    "timeMax": end_time,
                    "items": [{"id": cal_id} for cal_id in calendar_ids_to_check]
                }

                freebusy_result = self.service.freebusy().query(body=body).execute()

                # Extract busy times
                busy_times = []
                for cal_id, cal_data in freebusy_result.get('calendars', {}).items():
                    busy_times.extend(cal_data.get('busy', []))

                # Sort busy times
                busy_times.sort(key=lambda x: x['start'])

                # Find free slots
                free_slots = []
                current_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                slot_duration = timedelta(minutes=duration_minutes)

                for busy_slot in busy_times:
                    busy_start = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))

                    # If there's a gap before this busy slot
                    if current_time + slot_duration <= busy_start:
                        free_slots.append({
                            'start': current_time.isoformat(),
                            'end': busy_start.isoformat()
                        })

                    # Move current time to after this busy slot
                    busy_end = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
                    current_time = max(current_time, busy_end)

                # Check for free time after last busy slot
                if current_time + slot_duration <= end_dt:
                    free_slots.append({
                        'start': current_time.isoformat(),
                        'end': end_dt.isoformat()
                    })

                return free_slots
            except HttpError as e:
                raise Exception(f"Error finding free time: {e}")

        return await asyncio.to_thread(_find)
