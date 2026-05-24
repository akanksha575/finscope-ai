import asyncio
from django.apps import AppConfig
from utils.logger import log


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    
    def ready(self):
        """Initialize services when Django starts"""
        # Only run in main process (not in management commands or migrations)
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0] or 'uvicorn' in sys.argv[0]:
            log.info("FinScope AI API (Django) starting up...")
            
            # Initialize Redis cache connection (async, but we'll do it lazily)
            # Cache will be initialized on first use
            
            # Check for pre-trained documents (non-blocking, async)
            try:
                from utils.pretrain_init import check_and_pretrain_documents
                # Schedule async task (will run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(check_and_pretrain_documents(auto_ingest=False))
                    else:
                        loop.run_until_complete(check_and_pretrain_documents(auto_ingest=False))
                except RuntimeError:
                    # No event loop, will initialize lazily
                    pass
                log.info("Pre-training check scheduled")
            except Exception as e:
                log.warning(f"Could not initialize pre-training check: {e}")
