from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

@asynccontextmanager
async def life_span_handeler(app: FastAPI):
    logger.info("Server starting")
    yield
    logger.info("Server stopped")
