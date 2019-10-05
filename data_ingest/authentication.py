import logging
from rest_framework.authentication import TokenAuthentication

logger = logging.getLogger('ReVAL')


class TokenAuthenticationWithLogging(TokenAuthentication):
    def authenticate(self, request):
        logger.info(f'TokenAuthenticationWithLogging: authenticate')

        try:
            is_authenticated = super().authenticate(request)
            logger.info(f'is_authenticated: {is_authenticated}')
        except Exception as e:
            logger.error(f'is_authenticated: {e}')
            raise
        return is_authenticated
