from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment key
    path('payment_key/', views.generate_payment_key_view, name='generate-payment-key'),

    # Transactions
    path('pay/', views.create_transaction, name='create-transaction'),
    path('', views.list_transactions, name='list-transactions'),
    path('<uuid:transaction_id>/', views.get_transaction, name='get-transaction'),
]

# Refund URLs
refund_urlpatterns = [
    path('', views.create_refund, name='create-refund'),
    path('<uuid:refund_id>/', views.get_refund, name='get-refund'),
]
