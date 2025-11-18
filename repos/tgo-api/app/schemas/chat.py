"""Chat-related request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import Field

from app.schemas.base import BaseSchema


class StaffSendPlatformMessageRequest(BaseSchema):
    """Payload for staff-triggered outbound platform messages."""

    channel_id: str = Field(..., description="WuKongIM channel identifier (e.g., {visitor_id}-vtr)")
    channel_type: int = Field(
        ...,
        description="WuKongIM channel type (customer service chat uses 251)",
        example=251,
    )
    payload: Dict[str, Any] = Field(..., description="Platform message payload (matches Platform Service contract)")
    client_msg_no: Optional[str] = Field(
        None,
        description="Optional client-supplied idempotency key; generated when omitted",
    )


class ChatFileUploadResponse(BaseSchema):
    """Response for chat file upload."""

    file_id: str = Field(..., description="UUID of the uploaded file record")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="MIME type")
    file_url: str = Field(..., description="URL to access the file (e.g., /v1/chat/files/{file_id})")
    channel_id: str = Field(..., description="Channel identifier")
    channel_type: int = Field(..., description="Channel type code")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    uploaded_by: Optional[str] = Field(None, description="Staff username or 'visitor'")


# OpenAI-compatible Chat Completion schemas

class OpenAIChatMessage(BaseSchema):
    """OpenAI-compatible chat message."""

    role: Literal["system", "user", "assistant", "function"] = Field(
        ...,
        description="The role of the message author"
    )
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(None, description="The name of the author of this message")


class OpenAIChatCompletionRequest(BaseSchema):
    """Simplified chat completion request.

    Only includes essential fields: messages, stream, and user.
    """

    messages: List[OpenAIChatMessage] = Field(
        ...,
        description="A list of messages comprising the conversation so far"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream partial message deltas"
    )
    user: Optional[str] = Field(
        None,
        description="Unique identifier representing your end-user"
    )


class OpenAIChatCompletionChoice(BaseSchema):
    """OpenAI-compatible chat completion choice."""

    index: int = Field(..., description="The index of this choice")
    message: OpenAIChatMessage = Field(..., description="The generated message")
    finish_reason: Optional[str] = Field(
        None,
        description="Reason the model stopped generating tokens (stop, length, content_filter, null)"
    )


class OpenAIChatCompletionUsage(BaseSchema):
    """OpenAI-compatible token usage statistics."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class OpenAIChatCompletionResponse(BaseSchema):
    """OpenAI-compatible chat completion response.

    This schema is compatible with OpenAI's ChatGPT API format.
    See: https://platform.openai.com/docs/api-reference/chat/object
    """

    id: str = Field(..., description="Unique identifier for the chat completion")
    object: Literal["chat.completion"] = Field(
        default="chat.completion",
        description="Object type, always 'chat.completion'"
    )
    created: int = Field(..., description="Unix timestamp of when the completion was created")
    model: str = Field(..., description="The model used for completion")
    choices: List[OpenAIChatCompletionChoice] = Field(
        ...,
        description="List of completion choices"
    )
    usage: OpenAIChatCompletionUsage = Field(..., description="Token usage statistics")


# OpenAI-compatible streaming response schemas

class OpenAIChatCompletionDelta(BaseSchema):
    """OpenAI-compatible delta object for streaming responses."""

    role: Optional[Literal["system", "user", "assistant", "function"]] = Field(
        None,
        description="The role of the message author (only in first chunk)"
    )
    content: Optional[str] = Field(None, description="The content delta")


class OpenAIChatCompletionChunkChoice(BaseSchema):
    """OpenAI-compatible choice object for streaming responses."""

    index: int = Field(..., description="The index of this choice")
    delta: OpenAIChatCompletionDelta = Field(..., description="The delta content")
    finish_reason: Optional[str] = Field(
        None,
        description="Reason the model stopped generating tokens (stop, length, content_filter, null)"
    )


class OpenAIChatCompletionChunk(BaseSchema):
    """OpenAI-compatible streaming chunk response.

    This schema is compatible with OpenAI's ChatGPT API streaming format.
    See: https://platform.openai.com/docs/api-reference/chat/streaming
    """

    id: str = Field(..., description="Unique identifier for the chat completion")
    object: Literal["chat.completion.chunk"] = Field(
        default="chat.completion.chunk",
        description="Object type, always 'chat.completion.chunk'"
    )
    created: int = Field(..., description="Unix timestamp of when the completion was created")
    model: str = Field(..., description="The model used for completion")
    choices: List[OpenAIChatCompletionChunkChoice] = Field(
        ...,
        description="List of completion choices with delta content"
    )
