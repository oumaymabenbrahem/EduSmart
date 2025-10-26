# middlewares.py
from django.utils.deprecation import MiddlewareMixin

class FrameAllowMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Autoriser un site spécifique
        response['Content-Security-Policy'] = "frame-ancestors 'self' http://127.0.0.1:8000"
        return response
