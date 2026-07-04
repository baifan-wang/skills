"""Per-install User-Agent / contact-email helpers (legal Y12).

The stdio bio servers run on the END USER's machine, so the operator
identified to upstream APIs is the user, not Anthropic. These helpers read
the spawn-time env injected by the CLI's connector provider:

- ``OPERON_VERSION``       — product version (defaults to ``dev``);
- ``OPERON_INSTALL_ID``    — opaque per-install identifier (optional);
- ``OPERON_CONTACT_EMAIL`` — set ONLY when the user has affirmatively
  consented via the #contact-email-v2 flow (governing ``allowed`` row,
  current notice). Absent on declined/revoked/unset.

``product_ua`` assembles arXiv-ToU-style descriptive User-Agent strings.
``contact_email`` is the single read point for the consented address (or
``None`` — callers omit the param rather than send an empty string).
"""
from __future__ import annotations

import os


class ContactEmailRequired(RuntimeError):
    """Raised when an upstream's usage policy requires a contact email and
    none is available (no consent, no override). Tool wrappers catch this and
    return a structured ``{"error": "contact_email_required", ...}`` result."""


def contact_email() -> str | None:
    """User-consented contact email, or ``None`` when not provided."""
    return os.environ.get("OPERON_CONTACT_EMAIL") or None


def require_contact_email(*, env_override: str = "NCBI_EMAIL") -> str:
    """Return ``env_override`` > consented email; raise ``ContactEmailRequired``
    when neither yields a usable address. For upstreams (NCBI E-utilities)
    whose policy makes the contact mandatory rather than polite."""
    e = os.environ.get(env_override) or contact_email()
    if e and "@" in e:
        return e
    raise ContactEmailRequired(
        "This tool talks to NCBI E-utilities, which require a contact "
        "email per their usage policy. Enable 'Share contact email with "
        "research data services' in Settings → Privacy to provide one. "
        "If you've already enabled it, the connector picked up the setting "
        "before you approved — it will reconnect automatically; retry in a "
        "moment (or disable/re-enable the connector in Settings → Connectors). "
        f"(Advanced: if you run this server outside Claude Science, "
        f"set the {env_override} environment variable.)"
    )


class OpenAlexKeyRequired(RuntimeError):
    """Raised when a tool needs an OpenAlex API key and none is available.

    OpenAlex requires an api_key on ALL requests — there is no anonymous
    access and no mailto parameter; keyless production calls are
    unsupported.
    Tool wrappers catch this and return a structured
    ``{"error": "openalex_key_required", ...}`` result.
    """


def require_openalex_key() -> str:
    """Return the injected OpenAlex API key; raise ``OpenAlexKeyRequired``
    when absent. The CLI's connector provider injects ``OPENALEX_API_KEY``
    at spawn from the user's stored OpenAlex credential (and re-spawns this
    server when the credential changes)."""
    k = os.environ.get("OPENALEX_API_KEY") or None
    if k:
        return k
    raise OpenAlexKeyRequired(
        "OpenAlex requires a free API key for all requests (keyless calls "
        "are unsupported). Add one under Customize → Credentials → OpenAlex "
        "— create an OpenAlex account and copy the key from "
        "https://openalex.org/settings/api. After saving, this connector "
        "reconnects automatically; retry in a moment (or disable/re-enable "
        "it in Settings → Connectors). (Advanced: if you run this server "
        "outside Claude Science, set the OPENALEX_API_KEY environment "
        "variable.)"
    )


def product_ua(component: str, *, include_email: bool = True) -> str:
    """Descriptive per-install User-Agent for ``component``.

    Shape: ``operon-{component}/{ver} ({parts})`` where ``parts`` carries the
    install id and/or consented mailto, falling back to
    ``contact-not-provided`` when neither is available. A non-ASCII consented
    address is OMITTED from the UA (not lossy-rewritten — that could identify
    an unrelated mailbox); the raw address still goes out via the
    ``email=``/``mailto=`` query param. The whole UA is ASCII-sanitized as a
    final guard so the header is always latin-1-safe regardless of
    install-id/version content.
    """
    ver = os.environ.get("OPERON_VERSION", "dev")
    parts: list[str] = []
    install_id = os.environ.get("OPERON_INSTALL_ID")
    if install_id:
        parts.append(f"install:{install_id}")
    email = contact_email() if include_email else None
    if email and email.isascii():
        parts.append(f"mailto:{email}")
    if not parts:
        parts = ["contact-not-provided"]
    ua = f"operon-{component}/{ver} ({'; '.join(parts)})"
    return ua.encode("ascii", "ignore").decode()
