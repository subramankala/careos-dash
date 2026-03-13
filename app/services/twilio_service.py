from __future__ import annotations

from xml.sax.saxutils import escape


def twiml_message(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(body)}</Message></Response>'
