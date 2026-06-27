import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

# Start MQTT listener (non-blocking, daemon thread)
try:
    from dashboard.mqtt_client import get_client
    get_client()
except Exception:
    pass
