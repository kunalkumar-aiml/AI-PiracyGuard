"""Metadata forensics package for AI-PiracyGuard.

Provides extraction of video stream properties, codec metadata,
and identifies container anomalies.
"""

from piracyguard.core.metadata.video_metadata import MetadataAnalyzer, MetadataResult

__all__ = [
    "MetadataAnalyzer",
    "MetadataResult",
]
