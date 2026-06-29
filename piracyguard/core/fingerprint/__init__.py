"""Video fingerprinting engines for similarity forensics.

Provides standard hash functions (aHash, pHash, dHash) and temporal
sequence mapping for accurate duplicate detection and copy detection.
"""

from piracyguard.core.fingerprint.engine import FingerprintEngine, VideoFingerprint

__all__ = [
    "FingerprintEngine",
    "VideoFingerprint",
]
