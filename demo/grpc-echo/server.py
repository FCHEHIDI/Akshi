"""
Minimal TCP echo server — used to test SentinelOps TCP health checks.

The server accepts TCP connections on port 50051, reads up to 1024 bytes,
echoes them back, then closes the connection.

This is intentionally simple: SentinelOps TCP checks only need to
successfully open a connection (and optionally receive a response).

Usage:
    python server.py            # listens on 0.0.0.0:50051
    TCP_PORT=9000 python server.py
"""

import asyncio
import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("grpc-echo")

HOST: str = "0.0.0.0"
PORT: int = int(os.getenv("TCP_PORT", "50051"))

_connections: int = 0
_start_time: float = time.time()


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """
    Handle a single TCP connection.

    Args:
        reader: Asyncio stream reader for the client connection.
        writer: Asyncio stream writer for the client connection.
    """
    global _connections
    _connections += 1
    peer = writer.get_extra_info("peername")
    logger.info("Connection #%d from %s", _connections, peer)

    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        if data:
            logger.debug("Echo %d bytes to %s", len(data), peer)
            writer.write(data)
            await writer.drain()
    except asyncio.TimeoutError:
        logger.debug("No data received from %s within timeout — TCP-only check", peer)
    except ConnectionResetError:
        logger.debug("Connection reset by %s", peer)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def serve() -> None:
    """Start the TCP echo server and run until interrupted."""
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    logger.info("TCP echo server listening on %s:%s", addr[0], addr[1])

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Shutting down")
