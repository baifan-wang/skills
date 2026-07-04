"""interpro-domains: complete, deterministic protein -> InterPro domain-architecture retrieval."""

from .client import (
    AccessionNotFound,
    InterProClient,
    InterProError,
    fetch_domain_architecture,
)
from .summary import build_summary, summary_to_text

__version__ = "0.1.0"

__all__ = [
    "InterProClient",
    "InterProError",
    "AccessionNotFound",
    "fetch_domain_architecture",
    "build_summary",
    "summary_to_text",
    "__version__",
]
