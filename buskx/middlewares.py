# middlewares.py

from django.conf import settings


class LegalLinksMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.privacy_policy_link = settings.PRIVACY_POLICY_LINK
        request.terms_of_service_link = settings.TERMS_OF_SERVICE_LINK
        response = self.get_response(request)
        return response