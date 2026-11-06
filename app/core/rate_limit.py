from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage is enough for a single-process deployment. A multi-worker
# or multi-instance deployment should point this at Redis instead.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
