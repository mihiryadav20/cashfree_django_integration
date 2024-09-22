from django.urls import path
from . import views

urlpatterns = [
    path('create-payment/', views.create_payment, name='create_payment'), 
    path('payment/return/', views.payment_return, name='payment_return'),
    path('check-payment-status/', views.check_payment_status, name='check_payment_status'), 
    path('fetch-payment-status/', views.fetch_payment_status, name='fetch_payment_status'),
]
