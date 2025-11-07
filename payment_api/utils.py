import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def api_response(success=True, data=None, error=None, status_code=status.HTTP_200_OK):
    """
    Standardized API response format

    Args:
        success (bool): Whether the request was successful
        data (dict): Response data
        error (str/dict): Error message or details
        status_code (int): HTTP status code

    Returns:
        Response: DRF Response object with standardized format
    """
    response_data = {
        'success': success,
        'data': data,
        'error': error
    }
    return Response(response_data, status=status_code)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that returns standardized error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the error
        logger.error(
            f"API Error: {exc.__class__.__name__} - {str(exc)}",
            extra={'context': context}
        )

        # Customize the response format
        custom_response_data = {
            'success': False,
            'data': None,
            'error': {
                'message': str(exc),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data

    return response


def generate_api_key(length=32):
    """
    Generate a random API key

    Args:
        length (int): Length of the API key

    Returns:
        str: Random API key
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_payment_key():
    """
    Generate a unique payment key

    Returns:
        str: Unique payment key with prefix
    """
    import uuid
    return f"pk_{uuid.uuid4().hex[:24]}"
