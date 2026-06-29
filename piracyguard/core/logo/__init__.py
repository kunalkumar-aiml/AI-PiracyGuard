"""Logo and channel overlay detection for AI-PiracyGuard.

Provides template-based and contour-based logo area localization
to identify broadcaster watermarks and channel identifiers.
"""

from piracyguard.core.logo.logo_detector import LogoDetector, LogoResult

__all__ = [
    "LogoDetector",
    "LogoResult",
]
