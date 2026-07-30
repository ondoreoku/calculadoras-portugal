from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request

def get_ip():
    """Obtém o IP real do cliente"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

limiter = Limiter(
    key_func=get_ip,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://"
)
