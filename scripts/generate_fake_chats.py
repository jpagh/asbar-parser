#!/usr/bin/env python3
"""Generate a deterministic Android SMS Backup & Restore XML fixture.

The generated MMS image data is embedded in each ``image/png`` part, so the
fixture has no companion files and can be passed directly to ``asbar``.
"""

from __future__ import annotations

import argparse
import base64
import random
import struct
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence
from xml.etree import ElementTree as ET


CONTACTS = (
    ("Fixture Alice", "+12025550101"),
    ("Fixture Bob", "+12025550102"),
    ("Fixture Carol", "+12025550103"),
)

TEXT_TEMPLATES = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. {topic}.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. {topic}.",
    "Duis aute irure dolor in reprehenderit; {topic}.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. {topic}.",
)

TOPICS = (
    "the test conversation is looking good",
    "the fixture should cover ordinary text and media",
    "a deterministic sample makes debugging easier",
    "the parser can safely process this pretend message",
    "another synthetic update arrived from the test device",
    "the generated data is intentionally harmless and repeatable",
)

BASE_DATE = datetime(2025, 1, 15, 9, 0, tzinfo=timezone.utc)


def _contact_for(conversation_number: int) -> tuple[str, str]:
    if conversation_number < len(CONTACTS):
        return CONTACTS[conversation_number]
    return (
        f"Fixture Contact {conversation_number + 1}",
        f"+1202555{conversation_number + 101:04d}",
    )


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    """Return one well-formed PNG chunk."""
    chunk = chunk_type + payload
    return (
        struct.pack(">I", len(payload))
        + chunk
        + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
    )


def make_png(
    width: int, height: int, first: tuple[int, int, int], second: tuple[int, int, int]
) -> bytes:
    """Create a small RGB checkerboard PNG without requiring Pillow."""
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)  # PNG filter type: none
        for x in range(width):
            color = first if (x // 20 + y // 20) % 2 == 0 else second
            pixels.extend(color)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(pixels), level=9))
        + _png_chunk(b"IEND", b"")
    )


def _image_positions(message_count: int, image_count: int) -> set[int]:
    """Choose evenly spaced message indexes for image attachments."""
    image_count = min(image_count, message_count)
    if image_count == 0:
        return set()
    if image_count == 1:
        return {message_count // 2}
    return {
        index * (message_count - 1) // (image_count - 1) for index in range(image_count)
    }


def _epoch_milliseconds(moment: datetime) -> str:
    return str(int(moment.timestamp() * 1000))


def _readable_date(moment: datetime) -> str:
    return moment.strftime("%b %d, %Y %H:%M:%S")


def _message_attributes(
    address: str,
    contact_name: str,
    moment: datetime,
    sent: bool,
) -> dict[str, str]:
    timestamp = _epoch_milliseconds(moment)
    return {
        "protocol": "0",
        "address": address,
        "date": timestamp,
        "type": "2" if sent else "1",
        "subject": "null",
        "body": "",
        "toa": "null",
        "sc_toa": "null",
        "service_center": "null",
        "read": "1",
        "status": "-1",
        "locked": "0",
        "date_sent": timestamp,
        "readable_date": _readable_date(moment),
        "contact_name": contact_name,
    }


def _add_sms(
    root: ET.Element,
    address: str,
    contact_name: str,
    moment: datetime,
    body: str,
    sent: bool,
) -> None:
    attributes = _message_attributes(address, contact_name, moment, sent)
    attributes["body"] = body
    ET.SubElement(root, "sms", attributes)


def _add_mms(
    root: ET.Element,
    address: str,
    contact_name: str,
    moment: datetime,
    body: str,
    image_number: int,
    sent: bool,
    rng: random.Random,
    image_width: int,
    image_height: int,
) -> None:
    timestamp = _epoch_milliseconds(moment)
    message_id = f"fixture-{image_number:03d}"
    mms = ET.SubElement(
        root,
        "mms",
        {
            "date": timestamp,
            "rr": "129",
            "sub": "null",
            "ct_t": "application/vnd.wap.multipart.related",
            "m_id": message_id,
            "text_only": "0",
            "msg_box": "2" if sent else "1",
            "address": address,
            "contact_name": contact_name,
            "readable_date": _readable_date(moment),
            "date_sent": timestamp,
            "read": "1",
            "locked": "0",
        },
    )

    parts = ET.SubElement(mms, "parts")
    red = rng.randint(50, 210)
    green = rng.randint(50, 210)
    blue = rng.randint(50, 210)
    image = make_png(
        image_width,
        image_height,
        (red, green, blue),
        (255 - red, 255 - green, 255 - blue),
    )
    ET.SubElement(
        parts,
        "part",
        {
            "seq": "0",
            "ct": "image/png",
            "name": f"fixture-{image_number:03d}.png",
            "chset": "106",
            "cd": "null",
            "fn": f"fixture-{image_number:03d}.png",
            "cid": f"<fixture-{image_number:03d}@asbar>",
            "cl": f"fixture-{image_number:03d}.png",
            "data": base64.b64encode(image).decode("ascii"),
        },
    )
    ET.SubElement(
        parts,
        "part",
        {
            "seq": "1",
            "ct": "text/plain",
            "name": "null",
            "chset": "106",
            "text": body,
        },
    )

    addrs = ET.SubElement(mms, "addrs")
    ET.SubElement(
        addrs,
        "addr",
        {"address": address, "type": "151", "charset": "106"},
    )


def generate_fixture(
    output: Path,
    conversations: int = 2,
    messages_per_conversation: int = 10,
    images_per_conversation: int = 4,
    seed: int = 42,
    image_width: int = 640,
    image_height: int = 400,
) -> int:
    """Write a fixture and return the number of generated messages."""
    rng = random.Random(seed)
    root = ET.Element(
        "smses",
        {
            "count": "0",
            "backup_set": "asbar-fixture",
            "backup_date": _epoch_milliseconds(BASE_DATE),
        },
    )
    message_count = 0
    image_number = 0

    for conversation_number in range(conversations):
        contact_name, address = _contact_for(conversation_number)
        conversation_start = BASE_DATE + timedelta(days=conversation_number)
        image_positions = _image_positions(
            messages_per_conversation, images_per_conversation
        )

        for message_number in range(messages_per_conversation):
            moment = conversation_start + timedelta(minutes=message_number * 37)
            sent = message_number % 2 == 1
            topic = rng.choice(TOPICS)
            body = TEXT_TEMPLATES[message_number % len(TEXT_TEMPLATES)].format(
                topic=topic
            )

            if message_number in image_positions:
                image_number += 1
                _add_mms(
                    root,
                    address,
                    contact_name,
                    moment,
                    f"{body} Attached is fixture image {image_number}.",
                    image_number,
                    sent,
                    rng,
                    image_width,
                    image_height,
                )
            else:
                _add_sms(root, address, contact_name, moment, body, sent)
            message_count += 1

    root.set("count", str(message_count))
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output, encoding="utf-8", xml_declaration=True)
    return message_count


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("fake-chats.xml"),
        help="output XML path (default: fake-chats.xml)",
    )
    parser.add_argument(
        "--conversations",
        type=_positive_int,
        default=2,
        help="number of fake phone-number conversations (default: 2)",
    )
    parser.add_argument(
        "--messages",
        type=_positive_int,
        default=10,
        dest="messages_per_conversation",
        help="messages per conversation (default: 10)",
    )
    parser.add_argument(
        "--images",
        type=_positive_int,
        default=4,
        dest="images_per_conversation",
        help="images per conversation, capped at messages (default: 4)",
    )
    parser.add_argument(
        "--image-width",
        type=_positive_int,
        default=640,
        help="generated PNG width in pixels (default: 640)",
    )
    parser.add_argument(
        "--image-height",
        type=_positive_int,
        default=400,
        help="generated PNG height in pixels (default: 400)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for repeatable message text and image colors (default: 42)",
    )
    args = parser.parse_args(argv)

    message_count = generate_fixture(
        args.output,
        conversations=args.conversations,
        messages_per_conversation=args.messages_per_conversation,
        images_per_conversation=args.images_per_conversation,
        seed=args.seed,
        image_width=args.image_width,
        image_height=args.image_height,
    )
    print(
        f"Wrote {message_count} messages to {args.output} "
        f"({args.conversations} conversation(s), embedded PNG images)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
