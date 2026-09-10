#!/usr/bin/env python
"""Run the VAANI V2 API server with pre-bound IPv4 socket."""
import socket

import uvicorn
from app.main import app


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 8000))

    server = uvicorn.Server(
        config=uvicorn.Config(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=False,
        )
    )
    server.run(sockets=[sock])