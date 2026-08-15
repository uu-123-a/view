"""Production WSGI entrypoint for Waitress."""

from .app import create_app

app = create_app()
