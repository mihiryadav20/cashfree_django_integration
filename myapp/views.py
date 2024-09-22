import requests
import json  # Importing json module
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cashfree_Payment
import random
import string
import logging
from cashfree_pg.api_client import Cashfree

logger = logging.getLogger(__name__)

# Helper function to generate a unique 10-character alphanumeric order ID
def generate_order_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


@csrf_exempt
def create_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        customer_id = request.POST.get('customer_id')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email')

        if not all([amount, customer_id, customer_phone, customer_email]):
            logger.error('Missing required parameters')
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        order_id = generate_order_id()

        # Create a new payment record in the database
        payment = Cashfree_Payment.objects.create(
            order_id=order_id,
            amount=amount,
            customer_id=customer_id
        )

        # Prepare the payload for order creation
        payload = {
            "order_amount": float(amount),
            "order_currency": "INR",
            "order_id": order_id,
            "customer_details": {
                "customer_id": customer_id,
                "customer_phone": customer_phone
            },
            "order_meta": {
                "return_url": "https://www.azurro.online"
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-version': '2023-08-01',
            'x-client-id': settings.CASHFREE_APP_ID,
            'x-client-secret': settings.CASHFREE_SECRET_KEY,
        }

        # Make the POST request to Cashfree API
        response = requests.post('https://sandbox.cashfree.com/pg/orders', json=payload, headers=headers)
        logger.info(f"Raw response from Cashfree: {response.text}")

        try:
            response_data = response.json()
        except ValueError:
            logger.error("Response is not in JSON format")
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({'error': 'Received non-JSON response from Cashfree'}, status=500)

        if response_data.get('cf_order_id'):
            # Update the payment record with the Cashfree order ID
            payment.cf_order_id = response_data['cf_order_id']
            payment.save()

            return JsonResponse(response_data)
        else:
            logger.error(f"Payment creation failed: {response_data}")
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({'error': 'Payment creation failed or invalid response'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# NEW: Fetch payment status using the Cashfree API (instead of relying on webhooks)
@csrf_exempt
def fetch_payment_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        
        if not order_id:
            return JsonResponse({'error': 'Missing order_id'}, status=400)
        
        try:
            # Configure Cashfree API client
            Cashfree.XClientId = settings.CASHFREE_APP_ID
            Cashfree.XClientSecret = settings.CASHFREE_SECRET_KEY
            Cashfree.XEnvironment = Cashfree.SANDBOX  # Change to PRODUCTION when live
            x_api_version = "2023-08-01"

            # Call the Cashfree API to fetch the payment status
            api_response = Cashfree().PGOrderFetchPayments(x_api_version, order_id, None)

            if api_response.status_code == 200:
                payment_data = api_response.data
                logger.info(f"Full API response: {payment_data}")

                # Since the response is 200, we mark the payment status as 'SUCCESS'
                payment_status = 'SUCCESS'

                # Update payment status in the database
                payment = Cashfree_Payment.objects.get(order_id=order_id)
                payment.status = payment_status
                payment.save()

                logger.info(f"Updated payment status for order {order_id} to {payment_status}")
                return JsonResponse({'status': 'success', 'payment_status': payment_status}, status=200)
            else:
                # If the status code is anything other than 200, mark as 'FAILED'
                payment_status = 'FAILED'
                payment = Cashfree_Payment.objects.get(order_id=order_id)
                payment.status = payment_status
                payment.save()

                logger.error(f"Failed to fetch payment status for order {order_id}. Marking as 'FAILED'")
                return JsonResponse({'error': 'Failed to fetch payment status from Cashfree'}, status=500)

        except Cashfree_Payment.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            logger.error(f"Error fetching payment status from Cashfree: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)




def payment_return(request):
    # Process the payment confirmation here
    return HttpResponse("Thank you for your payment!")


@csrf_exempt
def check_payment_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('orderId')

        try:
            payment = Cashfree_Payment.objects.get(order_id=order_id)
            return JsonResponse({'status': payment.status})
        except Cashfree_Payment.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
