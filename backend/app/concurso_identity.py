"""Blank-ID definition shared by ingestion and database constraints."""

IDENTITY_WHITESPACE = ''.join(chr(i) for i in (*range(9, 14), *range(28, 33), 133, 160, 5760, *range(8192, 8203), 8232, 8233, 8239, 8287, 12288))


def identity_is_blank(value):
    return value is None or not str(value).strip(IDENTITY_WHITESPACE)


def identity_predicate(dialect, *, known):
    function = 'btrim' if dialect == 'postgresql' else 'trim'
    expression = f"{function}(external_id, '{IDENTITY_WHITESPACE}')"
    return (f"external_id IS NOT NULL AND {expression} <> ''" if known
            else f"external_id IS NULL OR {expression} = ''")
