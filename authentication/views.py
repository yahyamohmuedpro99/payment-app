from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from payment_api.utils import api_response
from .serializers import MerchantRegistrationSerializer, MerchantLoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new merchant"""
    serializer = MerchantRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        merchant = serializer.save()
        token, _ = Token.objects.get_or_create(user=merchant)

        return api_response(
            success=True,
            data={
                'email': merchant.email,
                'api_key': merchant.api_key,
                'token': token.key
            },
            status_code=status.HTTP_201_CREATED
        )

    return api_response(
        success=False,
        error=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login merchant and get token"""
    serializer = MerchantLoginSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        merchant = serializer.validated_data['merchant']
        token, _ = Token.objects.get_or_create(user=merchant)

        return api_response(
            success=True,
            data={
                'email': merchant.email,
                'api_key': merchant.api_key,
                'token': token.key
            }
        )

    return api_response(
        success=False,
        error=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )
