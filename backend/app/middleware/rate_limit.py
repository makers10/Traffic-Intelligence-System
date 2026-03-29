from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter instance — import this in routes that need limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
