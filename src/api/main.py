"""ASGI entrypoint for backend API."""

from src.core.app import create_app

app = create_app()
