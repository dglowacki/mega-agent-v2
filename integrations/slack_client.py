#!/usr/bin/env python3
"""
Slack Message Reader
Read messages from channels, DMs, and mentions.
"""

import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

class SlackMessageReader:
    """Read Slack messages, DMs, and mentions."""

    def __init__(self, workspace='flycow'):
        """Initialize Slack client."""
        workspace_lower = workspace.lower()
        if workspace_lower == 'flycow':
            token = os.getenv('SLACK_FLYCOW_ACCESS_TOKEN')
        elif workspace_lower == 'trailmix':
            token = os.getenv('SLACK_TRAILMIX_ACCESS_TOKEN')
        else:
            raise ValueError(f"Unknown workspace: {workspace}. Valid options: 'flycow', 'trailmix'")

        if not token:
            raise ValueError(f"Slack token not found for workspace '{workspace}'")

        self.client = WebClient(token=token)
        self.workspace = workspace_lower

        # Get authenticated user info
        auth = self.client.auth_test()
        self.user_id = auth['user_id']
        self.user_name = auth['user']
        self.team_name = auth['team']

    def get_all_channels(self):
        """Get all channels (public and private)."""
        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True
            )
            channels = response['channels']

            print(f"Found {len(channels)} channels:\n")
            for channel in channels:
                privacy = "🔒 Private" if channel['is_private'] else "# Public"
                members = channel.get('num_members', 0)
                print(f"  {privacy} {channel['name']} ({members} members)")
                print(f"    ID: {channel['id']}")

            return channels

        except SlackApiError as e:
            print(f"Error getting channels: {e.response['error']}")
            return []

    def get_channel_messages(self, channel_id, limit=10):
        """Get recent messages from a channel."""
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )

            messages = response['messages']

            # Get channel info
            channel_info = self.client.conversations_info(channel=channel_id)
            channel_name = channel_info['channel']['name']

            print(f"\nRecent messages in #{channel_name}:")
            print("-" * 80)

            for msg in reversed(messages):
                if msg.get('type') == 'message':
                    user = msg.get('user', 'Unknown')
                    text = msg.get('text', '')
                    ts = float(msg['ts'])
                    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                    # Get user name
                    try:
                        user_info = self.client.users_info(user=user)
                        user_name = user_info['user']['real_name']
                    except:
                        user_name = user

                    print(f"[{timestamp}] {user_name}: {text[:100]}")

            return messages

        except SlackApiError as e:
            print(f"Error getting messages: {e.response['error']}")
            return []

    def get_direct_messages(self, limit=20):
        """Get all direct message conversations."""
        try:
            # List DM conversations
            dm_response = self.client.conversations_list(types="im")
            dms = dm_response['channels']

            print(f"\nDirect Messages: {len(dms)} conversations")
            print("=" * 80)

            for dm in dms[:limit]:
                # Get conversation history
                history = self.client.conversations_history(
                    channel=dm['id'],
                    limit=1
                )

                if history['messages']:
                    last_msg = history['messages'][0]
                    text = last_msg.get('text', '')
                    ts = float(last_msg['ts'])
                    timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                    # Get other user's name
                    user_id = dm['user']
                    try:
                        user_info = self.client.users_info(user=user_id)
                        user_name = user_info['user']['real_name']
                        username = user_info['user']['name']
                    except:
                        user_name = user_id
                        username = user_id

                    print(f"\n💬 DM with {user_name} (@{username})")
                    print(f"   Last: [{timestamp}] {text[:80]}")

            return dms

        except SlackApiError as e:
            print(f"Error getting DMs: {e.response['error']}")
            return []

    def get_mentions(self, limit=20):
        """Get messages that mention you."""
        try:
            print(f"\nMessages mentioning @{self.user_name}:")
            print("=" * 80)

            # Search for mentions
            query = f"<@{self.user_id}>"
            response = self.client.search_messages(
                query=query,
                count=limit,
                sort='timestamp',
                sort_dir='desc'
            )

            matches = response['messages']['matches']

            if not matches:
                print("No mentions found.")
                return []

            print(f"Found {len(matches)} mentions:\n")

            for match in matches:
                text = match.get('text', '')
                ts = float(match['ts'])
                timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                # Get channel/user name
                channel_id = match.get('channel', {}).get('id')
                channel_name = match.get('channel', {}).get('name', 'Unknown')

                # Get sender
                user = match.get('user', match.get('username', 'Unknown'))

                print(f"📌 [{timestamp}] in #{channel_name}")
                print(f"   From: {user}")
                print(f"   {text[:150]}\n")

            return matches

        except SlackApiError as e:
            print(f"Error searching mentions: {e.response['error']}")
            return []

    def search_messages(self, query, limit=20, sort='timestamp', sort_dir='desc'):
        """Search for messages across all channels using Slack's search API.
        
        Args:
            query: Search query string (supports Slack search syntax)
            limit: Maximum number of results (default: 20)
            sort: Sort order ('timestamp' or 'score', default: 'timestamp')
            sort_dir: Sort direction ('asc' or 'desc', default: 'desc')
        
        Returns:
            List of matching messages with metadata
        """
        try:
            print(f"\n🔍 Searching Slack for: '{query}'")
            print("=" * 80)

            response = self.client.search_messages(
                query=query,
                count=limit,
                sort=sort,
                sort_dir=sort_dir
            )

            matches = response.get('messages', {}).get('matches', [])

            if not matches:
                print("No messages found.")
                return []

            print(f"Found {len(matches)} messages:\n")

            results = []
            for match in matches:
                text = match.get('text', '')
                ts = float(match['ts'])
                timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                # Get channel/user name
                channel_id = match.get('channel', {}).get('id', '')
                channel_name = match.get('channel', {}).get('name', 'Unknown')

                # Get sender
                user = match.get('user', match.get('username', 'Unknown'))

                result = {
                    'text': text,
                    'timestamp': timestamp,
                    'ts': match['ts'],
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'user': user,
                    'permalink': match.get('permalink', '')
                }
                results.append(result)

                print(f"📌 [{timestamp}] in #{channel_name}")
                print(f"   From: {user}")
                print(f"   {text[:150]}\n")

            return results

        except SlackApiError as e:
            print(f"Error searching messages: {e.response['error']}")
            return []

    def get_unread_messages(self):
        """Get unread message count."""
        try:
            # Get all conversations
            conversations = self.client.conversations_list(
                types="public_channel,private_channel,im",
                exclude_archived=True
            )

            unread_count = 0
            unread_channels = []

            for conv in conversations['channels']:
                # Get unread count for this conversation
                if conv.get('unread_count', 0) > 0:
                    unread_count += conv['unread_count']
                    unread_channels.append({
                        'name': conv.get('name', 'DM'),
                        'count': conv['unread_count'],
                        'id': conv['id']
                    })

            print(f"\n📬 Unread Messages: {unread_count} total")
            if unread_channels:
                print("\nChannels with unread messages:")
                for ch in unread_channels:
                    print(f"  - {ch['name']}: {ch['count']} unread")

            return unread_channels

        except SlackApiError as e:
            print(f"Error getting unread: {e.response['error']}")
            return []

    def get_user_by_email(self, email):
        """Look up a user by their email address."""
        try:
            response = self.client.users_lookupByEmail(email=email)
            return response['user']
        except SlackApiError as e:
            print(f"Error looking up user by email: {e.response['error']}")
            return None

    def send_dm_by_email(self, email, text):
        """Send a direct message to a user by their email address."""
        try:
            # Look up the user by email
            user = self.get_user_by_email(email)
            if not user:
                print(f"Could not find user with email: {email}")
                return None

            user_id = user['id']
            user_name = user.get('real_name', user.get('name', 'Unknown'))

            # Open a DM conversation with the user
            response = self.client.conversations_open(users=user_id)
            channel_id = response['channel']['id']

            # Send the message
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )

            ts = result['ts']
            print(f"✓ Message sent to {user_name} ({email})!")
            print(f"  Timestamp: {ts}")
            print(f"  Text: {text[:100]}...")

            return result

        except SlackApiError as e:
            print(f"Error sending DM: {e.response['error']}")
            return None

    def send_dm(self, recipient, text):
        """Send a direct message to a user.

        Args:
            recipient: User identifier - can be:
                      - User ID (e.g., "U12345678")
                      - @username (e.g., "@david")
                      - Email address (e.g., "user@example.com")
            text: Message text to send

        Returns:
            Slack API response or None if failed
        """
        try:
            user_id = None

            # If recipient starts with @, look up by username
            if recipient.startswith('@'):
                username = recipient[1:]  # Remove @
                users = self.list_all_users()
                for user in users:
                    if user.get('name') == username:
                        user_id = user['id']
                        break
                if not user_id:
                    print(f"Could not find user with username: {recipient}")
                    return None

            # If recipient looks like email (contains @), look up by email
            elif '@' in recipient and '.' in recipient:
                user = self.get_user_by_email(recipient)
                if user:
                    user_id = user['id']
                else:
                    print(f"Could not find user with email: {recipient}")
                    return None

            # Otherwise assume it's a user ID
            else:
                user_id = recipient

            # Open DM conversation
            response = self.client.conversations_open(users=user_id)
            channel_id = response['channel']['id']

            # Send message
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )

            ts = result['ts']
            print(f"✓ DM sent to {recipient}!")
            print(f"  Timestamp: {ts}")
            print(f"  Text: {text[:100]}...")

            return result

        except SlackApiError as e:
            print(f"Error sending DM: {e.response['error']}")
            return None

    def send_message_to_self(self, text):
        """Send a message to your own DM channel (message yourself)."""
        try:
            # Open a DM conversation with yourself
            response = self.client.conversations_open(users=self.user_id)
            channel_id = response['channel']['id']

            # Send the message
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )

            ts = result['ts']
            print(f"✓ Message sent to yourself!")
            print(f"  Timestamp: {ts}")
            print(f"  Text: {text}")

            return result

        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return None

    def send_message(self, channel_id, text):
        """Send a message to a specific channel or DM."""
        try:
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )

            ts = result['ts']
            print(f"✓ Message sent!")
            print(f"  Channel: {channel_id}")
            print(f"  Timestamp: {ts}")
            print(f"  Text: {text}")

            return result

        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return None

    def list_all_users(self, include_bots=False, include_deleted=False):
        """List all users in the workspace.
        
        Args:
            include_bots: Include bot users (default: False)
            include_deleted: Include deleted users (default: False)
        
        Returns:
            List of user dictionaries
        """
        try:
            users = []
            cursor = None
            
            while True:
                response = self.client.users_list(
                    cursor=cursor,
                    limit=200
                )
                
                batch = response.get('members', [])
                users.extend(batch)
                
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break
            
            # Filter based on options
            filtered_users = []
            for user in users:
                is_bot = user.get('is_bot', False)
                is_deleted = user.get('deleted', False)
                
                if not include_bots and is_bot:
                    continue
                if not include_deleted and is_deleted:
                    continue
                
                filtered_users.append(user)
            
            return filtered_users
            
        except SlackApiError as e:
            print(f"Error listing users: {e.response['error']}")
            return []

    def get_user_info(self, user_id):
        """Get detailed information about a user.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            User dictionary with detailed info
        """
        try:
            response = self.client.users_info(user=user_id)
            return response['user']
        except SlackApiError as e:
            print(f"Error getting user info: {e.response['error']}")
            return None

    def get_channel_members(self, channel_id):
        """Get all members of a channel.
        
        Args:
            channel_id: Slack channel ID
        
        Returns:
            List of user IDs in the channel
        """
        try:
            members = []
            cursor = None
            
            while True:
                response = self.client.conversations_members(
                    channel=channel_id,
                    cursor=cursor,
                    limit=200
                )
                
                batch = response.get('members', [])
                members.extend(batch)
                
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break
            
            return members
            
        except SlackApiError as e:
            print(f"Error getting channel members: {e.response['error']}")
            return []

    def invite_user_to_channel(self, channel_id, user_id):
        """Invite a user to a channel.
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID to invite
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.conversations_invite(
                channel=channel_id,
                users=user_id
            )
            return True
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            if error == 'already_in_channel':
                print(f"User is already in the channel")
                return True
            print(f"Error inviting user to channel: {error}")
            return False

    def remove_user_from_channel(self, channel_id, user_id):
        """Remove a user from a channel.
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.conversations_kick(
                channel=channel_id,
                user=user_id
            )
            return True
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error removing user from channel: {error}")
            return False

    def invite_user_to_workspace(self, email, channels=None, is_restricted=False, is_ultra_restricted=False):
        """Invite a user to the workspace (requires admin permissions).
        
        Args:
            email: Email address of user to invite
            channels: List of channel IDs to invite user to (optional)
            is_restricted: Create a restricted account (default: False)
            is_ultra_restricted: Create an ultra-restricted account (default: False)
        
        Returns:
            Invitation result or None if failed
        """
        try:
            # Note: This requires admin.users:write scope
            # The admin API may require different authentication
            params = {
                'email': email,
                'resend': True
            }
            
            if channels:
                params['channels'] = ','.join(channels)
            
            if is_restricted:
                params['restricted'] = True
            if is_ultra_restricted:
                params['ultra_restricted'] = True
            
            # Try admin.users.invite if available
            try:
                response = self.client.admin_users_invite(**params)
                return response
            except AttributeError:
                # Fallback to regular invite (may not work for new users)
                print("Note: admin.users.invite not available. May need admin scope.")
                return None
                
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error inviting user to workspace: {error}")
            return None

    def deactivate_user(self, user_id):
        """Deactivate a user in the workspace (requires admin permissions).
        
        Args:
            user_id: Slack user ID to deactivate
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: This requires admin.users:write scope
            try:
                self.client.admin_users_setRegular(user=user_id)
                return True
            except AttributeError:
                print("Note: admin.users API not available. May need admin scope.")
                return False
                
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error deactivating user: {error}")
            return False
    
    def set_user_as_full_member(self, user_id: str):
        """Set a restricted user as a full member (requires admin permissions).
        
        Args:
            user_id: Slack user ID to upgrade
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: This requires admin.users:write scope
            try:
                # Get team ID from auth
                team_id = self.client.auth_test()['team_id']
                
                # Set user as regular (full member)
                response = self.client.admin_users_setRegular(
                    team_id=team_id,
                    user_id=user_id
                )
                return response.get('ok', False)
            except AttributeError:
                print("Note: admin.users API not available. May need admin scope.")
                return False
                
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            if error == 'missing_scope' or 'not_allowed_token_type' in str(e):
                print(f"Error: Requires admin.users:write scope")
            else:
                print(f"Error setting user as full member: {error}")
            return False
        except Exception as e:
            print(f"Error: {str(e)[:150]}")
            return False
    
    def set_user_status(self, user_id: str, status_text: str = None, status_emoji: str = None, status_expiration: int = None):
        """Set a user's status (presence, status text, emoji).
        
        Args:
            user_id: Slack user ID
            status_text: Status text (e.g., "Working on a project")
            status_emoji: Status emoji (e.g., ":computer:")
            status_expiration: Unix timestamp when status expires (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            profile = {}
            if status_text is not None:
                profile['status_text'] = status_text
            if status_emoji is not None:
                profile['status_emoji'] = status_emoji
            if status_expiration is not None:
                profile['status_expiration'] = status_expiration
            
            if not profile:
                return False
            
            self.client.users_profile_set(
                user=user_id,
                profile=profile
            )
            return True
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error setting user status: {error}")
            return False
    
    def set_user_presence(self, presence: str):
        """Set your own presence (active/away).
        
        Args:
            presence: 'auto' (active) or 'away'
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.users_setPresence(presence=presence)
            return True
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error setting presence: {error}")
            return False
    
    def get_user_presence(self, user_id: str):
        """Get a user's presence status.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            Dict with presence info or None
        """
        try:
            response = self.client.users_getPresence(user=user_id)
            return response
        except SlackApiError as e:
            print(f"Error getting user presence: {e.response['error']}")
            return None
    
    def update_user_profile(self, user_id: str, **profile_fields):
        """Update a user's profile fields.
        
        Args:
            user_id: Slack user ID
            **profile_fields: Profile fields to update (e.g., first_name, last_name, 
                            display_name, real_name, email, phone, title, skype, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: Most profile fields require admin permissions
            self.client.users_profile_set(
                user=user_id,
                profile=profile_fields
            )
            return True
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error updating user profile: {error}")
            return False
    
    def set_user_as_admin(self, user_id: str):
        """Set a user as admin (requires owner permissions).
        
        Args:
            user_id: Slack user ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: This requires admin.users:write scope and owner permissions
            try:
                self.client.admin_users_setAdmin(user=user_id)
                return True
            except AttributeError:
                print("Note: admin.users API not available. May need owner permissions.")
                return False
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error setting user as admin: {error}")
            return False
    
    def remove_user_from_workspace(self, user_id: str):
        """Remove a user from the workspace (requires admin permissions).
        
        Args:
            user_id: Slack user ID to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: This requires admin.users:write scope
            try:
                self.client.admin_users_remove(user=user_id)
                return True
            except AttributeError:
                print("Note: admin.users API not available. May need admin scope.")
                return False
        except SlackApiError as e:
            error = e.response.get('error', 'unknown_error')
            print(f"Error removing user from workspace: {error}")
            return False
    
    def get_user_channels(self, user_id: str):
        """Get all channels a user is a member of.
        
        Args:
            user_id: Slack user ID
        
        Returns:
            List of channel dictionaries
        """
        try:
            # Get all channels
            all_channels = self.get_all_channels()
            
            # Filter channels where user is a member
            user_channels = []
            for channel in all_channels:
                members = self.get_channel_members(channel['id'])
                if user_id in members:
                    user_channels.append(channel)
            
            return user_channels
        except SlackApiError as e:
            print(f"Error getting user channels: {e.response['error']}")
            return []

    def upload_file(self, channel_id: str, file_path: str, title: str = None, initial_comment: str = None):
        """Upload a file to a Slack channel or DM.

        Args:
            channel_id: Channel or DM ID to upload to
            file_path: Path to the file to upload
            title: Optional title for the file
            initial_comment: Optional message to include with the file

        Returns:
            File upload result or None on error
        """
        try:
            result = self.client.files_upload_v2(
                channel=channel_id,
                file=file_path,
                title=title,
                initial_comment=initial_comment
            )

            if result.get('ok'):
                file_info = result.get('file', {})
                print(f"✓ File uploaded to {channel_id}")
                print(f"  Title: {title or file_info.get('name', 'Untitled')}")
                return result
            else:
                print(f"Error uploading file: {result}")
                return None

        except SlackApiError as e:
            print(f"Error uploading file: {e.response['error']}")
            return None

    def upload_file_to_user(self, recipient: str, file_path: str, title: str = None, initial_comment: str = None):
        """Upload a file to a user via DM.

        Args:
            recipient: @username, email, user ID, or 'self'
            file_path: Path to the file to upload
            title: Optional title for the file
            initial_comment: Optional message to include with the file

        Returns:
            File upload result or None on error
        """
        try:
            # Resolve recipient to user_id
            if recipient.lower() == 'self':
                user_id = self.user_id
            elif recipient.startswith('@'):
                username = recipient[1:]
                response = self.client.users_list()
                user_id = None
                for user in response['members']:
                    if user.get('name') == username:
                        user_id = user['id']
                        break
                if not user_id:
                    print(f"Could not find user: {recipient}")
                    return None
            elif '@' in recipient and '.' in recipient:
                user = self.get_user_by_email(recipient)
                if user:
                    user_id = user['id']
                else:
                    print(f"Could not find user with email: {recipient}")
                    return None
            else:
                user_id = recipient

            # Open DM conversation
            response = self.client.conversations_open(users=user_id)
            channel_id = response['channel']['id']

            # Upload file to the DM
            return self.upload_file(channel_id, file_path, title, initial_comment)

        except SlackApiError as e:
            print(f"Error uploading file to user: {e.response['error']}")
            return None


if __name__ == "__main__":
    print("FlyCow Slack Message Reader")
    print("=" * 80 + "\n")

    reader = SlackMessageReader('flycow')

    print(f"Authenticated as: @{reader.user_name}")
    print(f"Team: {reader.team_name}\n")

    # Get mentions
    reader.get_mentions(limit=10)

    # Get DMs
    reader.get_direct_messages(limit=5)

    # Get unread messages
    reader.get_unread_messages()

    # List all channels
    print("\n" + "=" * 80)
    channels = reader.get_all_channels()
