"""Conservative transport signature check; never repairs or rewrites bytes.

A header is not proof of a valid PDF. Bounded PDF parsing still follows.
Only up to16 leading ASCII space/tab/CR/LF bytes are accepted; raw hashing
and durable storage always use the unmodified transport payload.
"""


def has_pdf_header(content: bytes) -> bool:
    offset = 0
    while offset < len(content) and offset < 16 and content[offset] in b" \t\r\n":
        offset += 1
    return content[offset:offset + 5] == b"%PDF-"
