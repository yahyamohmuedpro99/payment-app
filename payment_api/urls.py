from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy', 'service': 'payment-api'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('authentication.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/transactions/', include('payments.urls')),
    path('api/refunds/', include(('payments.urls', 'payments'), namespace='refunds')),
    path('api/webhooks/', include('webhooks.urls')),
]
