import logging
from rest_framework.permissions import IsAuthenticated


logger = logging.getLogger(__name__)

class IsAuthenticatedWithLogging(IsAuthenticated):
    def has_permission(self, request, view):
        logger.info("IsAuthenticatedWithLogging: has_permission")
        logger.info(f'request user: {request.user}')
        logger.info(f'is_authenticated: {request.user.is_authenticated}')
        has_permission = super().has_permission(request, view)
        logger.info(f'has_permission: {has_permission}')
        return has_permission
