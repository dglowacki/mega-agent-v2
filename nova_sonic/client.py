"""
Nova Sonic Client

Wrapper for AWS Bedrock Runtime bidirectional streaming with Nova 2 Sonic.
Uses the experimental AWS SDK for Python.
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import AsyncIterator, Optional, Callable, Any

from . import config

logger = logging.getLogger(__name__)


class NovaSonicClient:
    """
    Client for Amazon Nova 2 Sonic bidirectional streaming.

    Handles:
    - Session initialization
    - Audio streaming (in/out)
    - Event parsing
    - Tool use coordination
    """

    def __init__(
        self,
        region: str = config.AWS_REGION,
        model_id: str = config.NOVA_MODEL_ID
    ):
        self.region = region
        self.model_id = model_id
        self.stream = None
        self.is_active = False
        self._event_handlers: dict[str, list[Callable]] = {}

        # Session identifiers
        self.prompt_name = None
        self.system_content_name = None
        self.audio_content_name = None

    async def connect(self) -> bool:
        """
        Establish bidirectional stream with Nova 2 Sonic.

        Returns:
            True if connection successful
        """
        try:
            # Import experimental SDK
            from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient
            from aws_sdk_bedrock_runtime.config import Config
            from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamOperationInput
            from smithy_aws_core.identity import EnvironmentCredentialsResolver
            from smithy_aws_core.auth import SigV4AuthScheme
            from aws_sdk_bedrock_runtime.auth import HTTPAuthSchemeResolver
            from smithy_core.shapes import ShapeID

            # Initialize client
            client_config = Config(
                endpoint_uri=config.BEDROCK_ENDPOINT,
                region=self.region,
                aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
                auth_scheme_resolver=HTTPAuthSchemeResolver(),
                auth_schemes={ShapeID("aws.auth#sigv4"): SigV4AuthScheme(service="bedrock")}
            )

            self.client = BedrockRuntimeClient(config=client_config)

            # Start bidirectional stream
            self.stream = await self.client.invoke_model_with_bidirectional_stream(
                InvokeModelWithBidirectionalStreamOperationInput(
                    model_id=self.model_id
                )
            )

            # Generate unique identifiers for this session
            self.prompt_name = str(uuid.uuid4())
            self.system_content_name = str(uuid.uuid4())
            self.audio_content_name = str(uuid.uuid4())

            self.is_active = True
            logger.info(f"Connected to Nova 2 Sonic ({self.model_id})")
            return True

        except ImportError as e:
            logger.error(f"Experimental AWS SDK not installed: {e}")
            logger.error("Install with: pip install git+https://github.com/awslabs/aws-sdk-python.git#subdirectory=clients/aws-sdk-bedrock-runtime")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Nova 2 Sonic: {e}")
            raise

    async def send_session_start(self, tools: list[dict] = None) -> None:
        """Send session initialization event with optional tools.

        Args:
            tools: List of tool definitions in Nova format
        """
        session_config = {
            "inferenceConfiguration": {
                "maxTokens": config.MAX_TOKENS,
                "topP": config.TOP_P,
                "temperature": config.TEMPERATURE
            }
        }

        # Tools must be configured in sessionStart for bidirectional streaming
        if tools:
            session_config["toolConfiguration"] = {
                "tools": tools,
                "toolChoice": {"auto": {}}
            }

        event = {
            "event": {
                "sessionStart": session_config
            }
        }
        await self._send_event(event)
        logger.debug(f"Sent sessionStart event (tools={len(tools) if tools else 0})")

    async def send_prompt_start(self) -> None:
        """
        Send prompt configuration with audio output settings.

        Note: Tools are configured in sessionStart for bidirectional streaming.
        """
        event = {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {
                        "mediaType": "text/plain"
                    },
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": config.AUDIO_OUTPUT_SAMPLE_RATE,
                        "sampleSizeBits": config.AUDIO_SAMPLE_SIZE_BITS,
                        "channelCount": config.AUDIO_CHANNELS,
                        "voiceId": config.VOICE_ID,
                        "encoding": config.AUDIO_ENCODING,
                        "audioType": config.AUDIO_TYPE
                    }
                }
            }
        }

        await self._send_event(event)
        logger.debug(f"Sent promptStart (promptName={self.prompt_name})")

    async def send_system_message(self, content: str) -> None:
        """Send system message content using proper content flow."""
        # contentStart for SYSTEM role
        await self._send_event({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.system_content_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "SYSTEM",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        })

        # textInput with the content
        await self._send_event({
            "event": {
                "textInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.system_content_name,
                    "content": content
                }
            }
        })

        # contentEnd
        await self._send_event({
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.system_content_name
                }
            }
        })
        logger.debug("Sent system message")

    async def send_audio_start(self) -> None:
        """Signal start of user audio input."""
        # Generate new audio content name for this turn
        self.audio_content_name = str(uuid.uuid4())

        await self._send_event({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": config.AUDIO_INPUT_SAMPLE_RATE,
                        "sampleSizeBits": config.AUDIO_SAMPLE_SIZE_BITS,
                        "channelCount": config.AUDIO_CHANNELS,
                        "audioType": "SPEECH",
                        "encoding": config.AUDIO_ENCODING
                    }
                }
            }
        })
        logger.debug("Sent audio contentStart")

    async def send_audio_chunk(self, audio_bytes: bytes) -> None:
        """
        Send audio chunk to Nova.

        Args:
            audio_bytes: Raw PCM audio data (16kHz, 16-bit, mono)
        """
        encoded = base64.b64encode(audio_bytes).decode('utf-8')
        await self._send_event({
            "event": {
                "audioInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "content": encoded
                }
            }
        })

    async def send_audio_end(self) -> None:
        """Signal end of user audio input."""
        await self._send_event({
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name
                }
            }
        })
        logger.debug("Sent audio contentEnd")

    async def send_tool_result(
        self,
        tool_use_id: str,
        result: Any
    ) -> None:
        """
        Send tool execution result back to Nova.

        Args:
            tool_use_id: ID from the toolUse event
            result: Tool execution result (will be JSON serialized)
        """
        content = json.dumps(result) if not isinstance(result, str) else result
        tool_result_content_name = str(uuid.uuid4())

        # contentStart for tool result
        await self._send_event({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": tool_result_content_name,
                    "type": "TOOL_RESULT",
                    "interactive": True,
                    "toolResultInputConfiguration": {
                        "toolUseId": tool_use_id,
                        "type": "TEXT",
                        "textInputConfiguration": {
                            "mediaType": "text/plain"
                        }
                    }
                }
            }
        })

        # textInput with tool result
        await self._send_event({
            "event": {
                "textInput": {
                    "promptName": self.prompt_name,
                    "contentName": tool_result_content_name,
                    "content": content
                }
            }
        })

        # contentEnd
        await self._send_event({
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": tool_result_content_name
                }
            }
        })
        logger.debug(f"Sent toolResult for {tool_use_id}")

    async def send_prompt_end(self) -> None:
        """Send prompt end event."""
        await self._send_event({
            "event": {
                "promptEnd": {
                    "promptName": self.prompt_name
                }
            }
        })
        logger.debug("Sent promptEnd")

    async def send_session_end(self) -> None:
        """Send session end event for graceful shutdown."""
        await self._send_event({
            "event": {
                "sessionEnd": {}
            }
        })
        logger.debug("Sent sessionEnd")
        self.is_active = False

    async def receive_events(self) -> AsyncIterator[dict]:
        """
        Receive and parse events from Nova.

        Yields:
            Parsed event dictionaries
        """
        if not self.stream:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamOutputChunk

            await self.stream.await_output()
            output_stream = self.stream.output_stream

            if output_stream is None:
                return

            async for out in output_stream:
                if not isinstance(out, InvokeModelWithBidirectionalStreamOutputChunk):
                    continue

                payload = out.value.bytes_
                if not payload:
                    continue

                event = json.loads(payload.decode('utf-8'))

                # Log event type
                event_type = self._get_event_type(event)
                logger.debug(f"Received event: {event_type}")

                yield event

                # Check for completion
                if "completionEnd" in event.get("event", {}):
                    break

        except Exception as e:
            if self.is_active:
                logger.error(f"Error receiving events: {e}")
                raise

    async def close(self) -> None:
        """Close the stream and cleanup."""
        if self.is_active:
            try:
                await self.send_session_end()
            except Exception as e:
                logger.warning(f"Error sending sessionEnd: {e}")

        if self.stream:
            try:
                await self.stream.input_stream.close()
            except Exception as e:
                logger.warning(f"Error closing stream: {e}")

        self.is_active = False
        self.stream = None
        logger.info("Nova Sonic client closed")

    async def _send_event(self, event: dict) -> None:
        """Send an event to Nova."""
        if not self.stream:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            from aws_sdk_bedrock_runtime.models import (
                InvokeModelWithBidirectionalStreamInputChunk,
                BidirectionalInputPayloadPart
            )

            event_json = json.dumps(event)
            chunk = InvokeModelWithBidirectionalStreamInputChunk(
                value=BidirectionalInputPayloadPart(
                    bytes_=event_json.encode('utf-8')
                )
            )
            await self.stream.input_stream.send(chunk)

        except Exception as e:
            logger.error(f"Error sending event: {e}")
            raise

    def _get_event_type(self, event: dict) -> str:
        """Extract event type from event dict."""
        if "event" in event:
            inner = event["event"]
            for key in inner:
                return key
        if "error" in event:
            return "error"
        return "unknown"


# Convenience function for creating a connected client
async def create_client() -> NovaSonicClient:
    """Create and connect a Nova Sonic client."""
    client = NovaSonicClient()
    await client.connect()
    return client
