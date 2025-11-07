from django.urls import path
from . import views

app_name = 'webhooks'

urlpatterns = [
    path('', views.create_webhook, name='create-webhook'),
    path('list/', views.list_webhooks, name='list-webhooks'),
    path('<uuid:webhook_id>/', views.delete_webhook, name='delete-webhook'),
]
