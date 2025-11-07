from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from payment_api.utils import api_response, generate_payment_key
from .models import Transaction, Refund
from .serializers import (
    TransactionSerializer, TransactionCreateSerializer,
    RefundSerializer, PaymentKeySerializer
)
from .tasks import process_transaction


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_payment_key_view(request):
    """Generate a payment key for transactions"""
    payment_key = generate_payment_key()
    serializer = PaymentKeySerializer({'payment_key': payment_key})

    return api_response(
        success=True,
        data=serializer.data,
        status_code=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    """Create a new transaction"""
    serializer = TransactionCreateSerializer(data=request.data)

    if serializer.is_valid():
        transaction = serializer.save(merchant=request.user)

        # Process transaction asynchronously
        process_transaction.delay(str(transaction.id))

        response_serializer = TransactionSerializer(transaction)
        return api_response(
            success=True,
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return api_response(
        success=False,
        error=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_transactions(request):
    """List all transactions for the authenticated merchant"""
    transactions = Transaction.objects.filter(merchant=request.user)

    # Apply pagination
    paginator = TransactionPagination()
    result_page = paginator.paginate_queryset(transactions, request)
    serializer = TransactionSerializer(result_page, many=True)

    return paginator.get_paginated_response({
        'success': True,
        'data': serializer.data,
        'error': None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction(request, transaction_id):
    """Get a specific transaction"""
    try:
        transaction = Transaction.objects.get(
            id=transaction_id,
            merchant=request.user
        )
        serializer = TransactionSerializer(transaction)

        return api_response(
            success=True,
            data=serializer.data
        )

    except Transaction.DoesNotExist:
        return api_response(
            success=False,
            error='Transaction not found',
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_refund(request):
    """Create a refund for a transaction"""
    serializer = RefundSerializer(data=request.data)

    if serializer.is_valid():
        # Verify transaction belongs to merchant
        transaction = serializer.validated_data['transaction']
        if transaction.merchant != request.user:
            return api_response(
                success=False,
                error='Transaction not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        refund = serializer.save()
        # Mark refund as succeeded immediately (simplified)
        from django.utils import timezone
        refund.status = 'succeeded'
        refund.processed_at = timezone.now()
        refund.save()

        response_serializer = RefundSerializer(refund)
        return api_response(
            success=True,
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return api_response(
        success=False,
        error=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_refund(request, refund_id):
    """Get a specific refund"""
    try:
        refund = Refund.objects.select_related('transaction').get(
            id=refund_id,
            transaction__merchant=request.user
        )
        serializer = RefundSerializer(refund)

        return api_response(
            success=True,
            data=serializer.data
        )

    except Refund.DoesNotExist:
        return api_response(
            success=False,
            error='Refund not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
