"""Technical-id (slug) generation for rules and groups.

An ``id`` is the stable, machine-facing identity of a rule or group. It is
derived from the display ``name`` the way a blog post's URL alias is derived
from its title: lower-cased ASCII words joined by hyphens, never starting with
a digit. The display name stays free-form and user-visible (and could later be
translated), while the id remains fixed and is what other rules/groups
reference.
"""

import re
import unicodedata


_ID_CHARS = re.compile(r'[A-Za-z0-9]+')


def make_slug(text, fallback='x'):
    """Normalize a display name into an id-shaped slug.

    Accented letters are folded to their ASCII base (``é`` -> ``e``), runs of
    anything that is not an ASCII letter/digit become a single ``-``, the result
    is lower-cased, and a slug that would otherwise start with a digit is
    prefixed with ``fallback`` so it never starts with a number. A name with no
    usable characters falls back to ``fallback`` itself.
    """
    text = f'{text}' if text is not None else ''
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    parts = _ID_CHARS.findall(text.lower())
    slug = '-'.join(parts)
    if not slug:
        slug = f'{fallback}'
    elif slug[0].isdigit():
        slug = f'{fallback}-{slug}'
    return slug


def unique_slug(text, existing, fallback='x'):
    """``make_slug(text)`` made unique against the ``existing`` set of ids.

    On a collision, appends ``-2``, ``-3``, … until a free id is found (the same
    behavior blog engines use for duplicate URL aliases).
    """
    base = make_slug(text, fallback=fallback)
    return ensure_unique(base, existing)


def ensure_unique(base, existing):
    """Return ``base`` unchanged, or with ``-2``/``-3``/… appended when it collides.

    Unlike :func:`unique_slug` this does **not** normalize ``base`` — it assumes
    the caller already has a canonical id and only needs deduplication, so an
    explicitly-provided id keeps its exact spelling.
    """
    candidate = base
    n = 2
    while candidate in existing:
        candidate = f'{base}-{n}'
        n += 1
    return candidate


def is_valid_id(value):
    """Return True when ``value`` is an id-shaped string.

    An id is a non-empty run of ASCII letters, digits and hyphens that does not
    start with a digit (so it is safe as a URL path segment and as a technical
    identifier).
    """
    if value is None:
        return False
    return bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', f'{value}'))
