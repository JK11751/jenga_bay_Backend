from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_daraja.mpesa.core import MpesaClient
import json

@csrf_exempt
def index(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            amount = data.get('amount')

            if not phone_number or not amount:
                return JsonResponse({'error': 'Phone number and amount are required.'}, status=400)

            # Ensure amount is an integer
            try:
                amount = int(amount)
            except ValueError:
                return JsonResponse({'error': 'Amount must be an integer'}, status=400)

            cl = MpesaClient()
            account_reference = 'reference'
            transaction_desc = 'Payment Description'
            callback_url = 'https://precious-adversely-prawn.ngrok-free.app/mpesa/daraja/stk-push'  # Update with your backend callback URL

            # Call the STK push method
            response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)

            # Log the response for debugging
            print("Mpesa Response:", response)

            # Convert the response to a dictionary if it's not already
            if isinstance(response, dict):
                return JsonResponse(response)
            else:
                return JsonResponse({'error': 'Unexpected response format from Mpesa'}, status=500)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return HttpResponse('Method Not Allowed', status=405)


@csrf_exempt
def stk_push_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Print the data to the server logs for debugging
            print("Callback data:", data)

            # Return the data in the response for verification
            return JsonResponse(data, safe=False, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return HttpResponse("STK Push Callback Endpoint", status=200)
