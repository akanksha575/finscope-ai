#!/usr/bin/env python
"""
Run Django server with Daphne for WebSocket support
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

if __name__ == "__main__":
    from daphne.server import Server
    from daphne.endpoints import build_endpoint_description_strings
    from django_app.asgi import application
    
    # Run with Daphne
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
    
    print(f"Starting Daphne server on {host}:{port}")
    print("WebSocket support enabled at ws://{host}:{port}/api/research/stream")
    
    from daphne.cli import CommandLineInterface
    CommandLineInterface().run(["django_app.asgi:application", "-b", host, "-p", str(port)])
