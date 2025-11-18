from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
import base64
import json
from typing import Optional


try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except Exception:  # ImportError or env issues
    HAS_CRYPTO = False


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        return data
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 32:
        # Invalid padding; return as-is to fail downstream
        return data
    return data[:-pad_len]


def _wecom_decrypt_message(encrypt_b64: str, encoding_aes_key: str, receiveid_expected: str) -> Optional[str]:
    """Decrypt WeCom encrypted message using AES-256-CBC PKCS7.

    Returns the decrypted inner XML string on success, or None on failure.
    """
    try:
        aes_key = base64.b64decode(encoding_aes_key + "=")  # 43 chars -> 32 bytes
        iv = aes_key[:16]
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        ciphertext = base64.b64decode(encrypt_b64)
        padded_plain = decryptor.update(ciphertext) + decryptor.finalize()
        plain = _pkcs7_unpad(padded_plain)
        if len(plain) < 20:
            return None
        # 16 bytes random, 4 bytes msg_len (big-endian), then xml, then receiveid
        msg_len = int.from_bytes(plain[16:20], "big")
        xml_bytes = plain[20:20 + msg_len]
        receiveid = plain[20 + msg_len:].decode("utf-8", errors="ignore")
        if receiveid_expected and receiveid_expected != receiveid:
            return None
        return xml_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return None

from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import get_db
from app.db.models import Platform, WeComInbox, WuKongIMInbox
from app.api.error_utils import error_response, get_request_id
from app.api.schemas import ErrorResponse

router = APIRouter()


def _sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def compute_msg_signature(token: str, timestamp: str, nonce: str, msg: str | None = None) -> str:
    """Compute WeCom msg_signature = sha1(sort(token, timestamp, nonce, msg_encrypt_or_echostr)).
    When msg is None (plain mode POST w/o Encrypt), use only token/timestamp/nonce.
    """
    parts = [token, timestamp, nonce]
    if msg is not None:
        parts.append(msg)
    parts.sort()
    return _sha1_hex("".join(parts))



# --- WeCom helpers (moved to dedicated module) ---
from app.api.wecom_utils import build_xml_raw_payload, sync_kf_messages

async def _handle_wecom_webhook(platform: Platform, request: Request, db: AsyncSession) -> dict[str, Any] | Response:
    """Handle WeCom webhook POST callback for a given platform.

    Producer stage: validate request, parse XML, and persist a WeComInbox row.

    Returns a JSON dict or Response to be sent to the client.
    """
    config = platform.config or {}
    token = (config.get("token") or "")

    # Query params for signature verification
    query = request.query_params
    msg_signature = query.get("msg_signature")
    timestamp = query.get("timestamp") or ""
    nonce = query.get("nonce") or ""

    raw_body = await request.body()
    body_text = raw_body.decode("utf-8") if raw_body else ""
    print("body_text---->",body_text)

    # Very minimal XML parsing (plain mode). Encrypted mode contains <Encrypt>...
    try:
        root = ET.fromstring(body_text)
    except Exception:
        return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_PAYLOAD", message="Invalid XML payload", request_id=get_request_id(request))

    encrypt_node = root.findtext("Encrypt")

    # Verify signature and prepare XML root to parse
    xml_root = root
    decrypted_xml_text = None

    if encrypt_node:
        # Encrypted mode signature includes Encrypt
        if not (token and msg_signature):
            return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_SIGNATURE", message="Missing or invalid signature parameters", request_id=get_request_id(request))
        expected = compute_msg_signature(token, timestamp, nonce, encrypt_node)
        if expected != msg_signature:
            return error_response(status.HTTP_403_FORBIDDEN, code="SIGNATURE_MISMATCH", message="Signature verification failed", request_id=get_request_id(request))

        # Decrypt using encoding_aes_key from config
        encoding_aes_key = (config.get("encoding_aes_key") or "").strip()
        corp_id = (config.get("corp_id") or "").strip()
        if not HAS_CRYPTO:
            return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, code="CRYPTO_LIBRARY_MISSING", message="cryptography library is not installed on server")
        if not encoding_aes_key:
            return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, code="ENCRYPTION_CONFIG_MISSING", message="encoding_aes_key is not configured for this WeCom platform")

        decrypted_xml_text = _wecom_decrypt_message(encrypt_node, encoding_aes_key, corp_id)
        if not decrypted_xml_text:
            return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_PAYLOAD", message="Failed to decrypt WeCom message")
        try:
            print("decrypted_xml_text---->",decrypted_xml_text)
            xml_root = ET.fromstring(decrypted_xml_text)
        except Exception:
            return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_PAYLOAD", message="Decrypted XML is invalid")
    else:
        # Plain mode signature without Encrypt
        if not (token and msg_signature):
            return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_SIGNATURE", message="Missing or invalid signature parameters", request_id=get_request_id(request))
        expected = compute_msg_signature(token, timestamp, nonce)
        if expected != msg_signature:
            return error_response(status.HTTP_403_FORBIDDEN, code="SIGNATURE_MISMATCH", message="Signature verification failed", request_id=get_request_id(request))

    # Extract fields from the appropriate XML root (decrypted or plain)
    msg_type = xml_root.findtext("MsgType") or ""
    from_user = xml_root.findtext("FromUserName") or ""
    content = xml_root.findtext("Content") or ""
    message_id = xml_root.findtext("MsgId") or ""
    create_time_raw = xml_root.findtext("CreateTime") or ""

    # Convert CreateTime (epoch seconds) to timezone-aware datetime
    received_at = None
    try:
        ts = int(create_time_raw)
        received_at = datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        received_at = None

    # Handle event-type callbacks (currently focusing on kf_msg_or_event)

    if (msg_type or "").lower() == "event":
        # Specifically handle KF event notification: kf_msg_or_event -> trigger sync, do not store event itself
        token_val = xml_root.findtext("Token") or ""
        open_kf_id_for_cursor = xml_root.findtext("OpenKfId") or ""
        open_kf_id_for_cursor = open_kf_id_for_cursor or (xml_root.findtext("ToUserName") or "")

        try:
            cfg = platform.config or {}
            corp_id = (cfg.get("corp_id") or "").strip()
            app_secret = (cfg.get("app_secret") or "").strip()
            # Fire-and-forget style sync; but await to complete current batch with a safety loop
            if token_val and corp_id and app_secret and open_kf_id_for_cursor:
                await sync_kf_messages(corp_id=corp_id, app_secret=app_secret, event_token=token_val, open_kf_id=open_kf_id_for_cursor, platform_id=platform.id, db=db)
            else:
                logging.warning("[WECOM] KF event missing required fields (token/corp_id/app_secret/open_kf_id)")
        except Exception as e:
            logging.error("[WECOM] KF event sync failed: %s", e)
        # Always acknowledge the event quickly
        return {"ok": True}

    # Store inbound message into wecom_inbox (producer stage)
    try:
        raw_payload = build_xml_raw_payload(
            raw_xml=body_text,
            decrypted_xml=decrypted_xml_text,
            parsed={
                "MsgType": msg_type,
                "FromUserName": from_user,
                "MsgId": message_id,
                "CreateTime": create_time_raw,
                "Content": content,
            },
        )

        # Extract OpenKfId if present in callback (may be absent for internal messages)
        open_kfid_val = xml_root.findtext("OpenKfId") or None

        # Store inbound text message
        inbox_record = WeComInbox(
            platform_id=platform.id,
            message_id=message_id or "",
            from_user=from_user,
            open_kfid=open_kfid_val,
            msg_type=msg_type,
            content=content or "",
            is_from_colleague=True,
            raw_payload=raw_payload,
            status="pending",
            received_at=received_at,
        )
        db.add(inbox_record)
        await db.commit()
    except IntegrityError as e:
        # Duplicate delivery; already stored. Treat as success.
        print(f"[WECOM] Duplicate message detected for {platform.id}: {e}")
        await db.rollback()
    except Exception as e:
        print(f"[WECOM] Store raw message failed for {platform.id}: {e}")
        await db.rollback()
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Immediate 200 OK; WeCom expects a fast response.
    return {"ok": True}


async def _handle_wukongim_webhook(
    platform: Platform,
    request: Request,
    db: AsyncSession,
    messages: Optional[list[dict[str, Any]]] = None,
    event: Optional[str] = None,
) -> dict[str, Any] | Response:
    """Handle WuKongIM webhook POST callback for a website platform.

    According to WuKongIM docs:
    - The event is provided via query parameter `event` (e.g., msg.notify)
    - The request body is a JSON array of message objects

    Producer stage: iterate messages and store a WuKongIMInbox row for each.
    """
    event = event or request.query_params.get("event")
    if event != "msg.notify":
        # Ignore non-message events but reply OK to acknowledge
        return {"ok": True}

    # Body is a JSON array of messages
    if messages is None:
        try:
            messages = await request.json()
        except Exception:
            return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_PAYLOAD", message="Invalid JSON payload", request_id=get_request_id(request))

    if not isinstance(messages, list):
        return error_response(status.HTTP_400_BAD_REQUEST, code="INVALID_PAYLOAD", message="Expected an array of messages", request_id=get_request_id(request))

    for message in messages:
        if not isinstance(message, dict):
            continue  # skip invalid entries
        try:
            message_id = str(message.get("message_id"))
            client_msg_no = message.get("client_msg_no")
            from_uid = str(message.get("from_uid") or "")
            channel_id = str(message.get("channel_id") or "")
            channel_type = int(message.get("channel_type") or 0)
            message_seq = int(message.get("message_seq")) if message.get("message_seq") is not None else 0
            timestamp = int(message.get("timestamp") or 0)
            payload_b64 = str(message.get("payload") or "")
            platform_open_id = message.get("platform_open_id")  # Extract platform_open_id
        except Exception:
            # Skip this message if fields are malformed
            continue

        # Skip messages sent by staff/customer service (from_uid suffix "-staff")
        if from_uid and from_uid.endswith("-staff"):
            logging.info("[WUKONGIM] Skipping staff message: from_uid=%s message_id=%s", from_uid, message_id)
            continue

        # Required minimal fields
        if not (message_id and from_uid and channel_id and channel_type and payload_b64):
            continue

        try:
            # Store decoded payload (plain text/JSON) instead of base64
            try:
                content_bytes = base64.b64decode(payload_b64 or "") if payload_b64 else b""
                decoded_payload = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                decoded_payload = ""

            inbox_record = WuKongIMInbox(
                platform_id=platform.id,
                message_id=message_id,
                client_msg_no=client_msg_no,
                from_uid=from_uid,
                channel_id=channel_id,
                channel_type=channel_type,
                message_seq=message_seq,
                timestamp=timestamp,
                payload=decoded_payload,
                platform_open_id=platform_open_id,
                raw_body=message,
                status="pending",
                retry_count=0,
                fetched_at=datetime.now(timezone.utc),
            )
            db.add(inbox_record)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Duplicate; treat as success for that one message
            continue
        except Exception:
            await db.rollback()
            # If one message fails to store, continue with others; overall ack OK
            continue

    return {"ok": True}




@router.post("/v1/platforms/callback/{platform_api_key}", responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 501: {"model": ErrorResponse}})
async def platforms_callback(platform_api_key: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Unified platform callback endpoint for WeCom and WuKongIM.

    - For WeCom: validate signature, parse XML, store to wecom_inbox
    - For WuKongIM (platform type 'website'): read `event` from query, parse body array, store to wukongim_inbox
    """
    # Lookup platform by api_key
    platform = await db.scalar(
        select(Platform).where(Platform.api_key == platform_api_key, Platform.is_active.is_(True))
    )
    if not platform:
        logging.warning("Callback for unknown platform: %s", platform_api_key)
        return error_response(status.HTTP_404_NOT_FOUND, code="PLATFORM_NOT_FOUND", message="Platform not found", request_id=get_request_id(request))

    platform_type = (platform.type or "").lower()

    # Platform-type-specific routing
    if platform_type == "wecom":
        return await _handle_wecom_webhook(platform=platform, request=request, db=db)
    if platform_type == "website":
        return await _handle_wukongim_webhook(platform=platform, request=request, db=db)

    # Unsupported platform type for this endpoint
    return error_response(status.HTTP_404_NOT_FOUND, code="PLATFORM_TYPE_UNSUPPORTED", message=f"Unsupported platform type: {platform.type}", request_id=get_request_id(request))

