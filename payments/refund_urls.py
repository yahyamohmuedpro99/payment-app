from django.urls import path
from . import views

app_name = 'refunds'

urlpatterns = [
    path('', views.create_refund, name='create-refund'),
    path('<uuid:refund_id>/', views.get_refund, name='get-refund'),
]
