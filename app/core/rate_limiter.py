"""
PM Digital Employee - Rate Limiting Configuration
Rate limiting for Lark webhook and callback endpoints.

Note: slowapi uses in-memory storage by default, which means rate limits
are per-process. For multi-replica deployments, configure a Redis backend.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global rate limiter instance
limiter = Limiter(key_func=get_remote_address)
