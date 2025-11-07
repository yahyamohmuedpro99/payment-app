from rest_framework import serializers
from .models import Transaction, Refund
from payment_api.utils import generate_payment_key
from decimal import Decimal


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""

    merchant_email = serializers.EmailField(source='merchant.email', read_only=True)
    is_refundable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'merchant_email', 'amount', 'currency', 'description',
            'status', 'payment_key', 'failure_reason', 'is_refundable',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'status', 'payment_key', 'failure_reason',
            'created_at', 'updated_at', 'processed_at', 'merchant_email', 'is_refundable'
        ]

    def validate_amount(self, value):
        """Validate transaction amount"""
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than 0')
        if value > Decimal('1000000'):
            raise serializers.ValidationError('Amount exceeds maximum limit')
        return value


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""

    class Meta:
        model = Transaction
        fields = ['amount', 'currency', 'description']

    def validate_amount(self, value):
        """Validate transaction amount"""
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than 0')
        if value > Decimal('1000000'):
            raise serializers.ValidationError('Amount exceeds maximum limit')
        return value

    def create(self, validated_data):
        """Create transaction with payment key"""
        validated_data['payment_key'] = generate_payment_key()
        return super().create(validated_data)


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for refunds"""

    transaction_payment_key = serializers.CharField(source='transaction.payment_key', read_only=True)
    transaction_amount = serializers.DecimalField(
        source='transaction.amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    currency = serializers.CharField(source='transaction.currency', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id', 'transaction', 'transaction_payment_key', 'transaction_amount',
            'amount', 'currency', 'reason', 'status',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at', 'processed_at',
            'transaction_payment_key', 'transaction_amount', 'currency'
        ]

    def validate(self, data):
        """Validate refund data"""
        transaction = data.get('transaction')
        amount = data.get('amount')

        # Check if transaction exists and is succeeded
        if transaction.status != 'succeeded':
            raise serializers.ValidationError({
                'transaction': 'Can only refund succeeded transactions'
            })

        # Check if already refunded
        if hasattr(transaction, 'refund'):
            raise serializers.ValidationError({
                'transaction': 'Transaction already has a refund'
            })

        # Validate refund amount
        if amount > transaction.amount:
            raise serializers.ValidationError({
                'amount': f'Refund amount cannot exceed transaction amount ({transaction.amount})'
            })

        if amount <= Decimal('0'):
            raise serializers.ValidationError({
                'amount': 'Refund amount must be greater than 0'
            })

        return data


class PaymentKeySerializer(serializers.Serializer):
    """Serializer for payment key generation"""

    payment_key = serializers.CharField(read_only=True)
