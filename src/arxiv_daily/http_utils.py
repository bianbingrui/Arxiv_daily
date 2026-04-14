from __future__ import annotations

from pathlib import Path
import os
import ssl


def build_ssl_context() -> ssl.SSLContext:
    ssl_cert_file = os.getenv("SSL_CERT_FILE")
    if ssl_cert_file and Path(ssl_cert_file).exists():
        return ssl.create_default_context(cafile=ssl_cert_file)

    fallback_paths = [
        Path("/etc/ssl/cert.pem"),
        Path("/usr/local/etc/openssl@3/cert.pem"),
        Path("/Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/cert.pem"),
    ]
    for path in fallback_paths:
        if path.exists():
            return ssl.create_default_context(cafile=str(path))

    return ssl.create_default_context()
