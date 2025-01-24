import json
import requests
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_http_methods(["POST"])
@csrf_exempt
def charge_view(request):
    try:
        charge = stripe.Charge.create(
            amount=request.POST.get("amount", ""),
            currency=request.POST.get("currency", ""),
            source=request.POST.get("source", ""),
        )
        if charge["status"] == "succeeded":
            return HttpResponse(
                json.dumps({"message": "Your transaction has been successful."})
            )
        else:
            raise stripe.error.CardError

    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        body = e.json_body
        err = body.get("error", {})
        print("Status is: %s" % e.http_status)
        print("Type is: %s" % err.get("type"))
        print("Code is: %s" % err.get("code"))
        print("Message is %s" % err.get("message"))
        return HttpResponse(
            json.dumps({"message": err.get("message")}), status=e.http_status
        )

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        return HttpResponse(json.dumps({"message": "Too many requests to the API."}))

    except stripe.error.InvalidRequestError as e:
        # invalid parameters were supplied to Stripe"s API
        return HttpResponse(json.dumps({"message": "Invalid parameters."}))

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe"s API failed
        # (maybe you changed API keys recently)
        return HttpResponse(json.dumps({"message": "Authentication failed."}))

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        return HttpResponse(
            json.dumps({"message": "Network communication failed, try again."})
        )

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe
        # send yourself an email
        return HttpResponse(json.dumps({"message": "Provider error!"}))

    # Something else happened, completely unrelated to Stripe
    except Exception as e:
        return HttpResponse(
            json.dumps({"message": "Unable to process payment, try again."})
        )

@require_http_methods(["POST"])
@csrf_exempt
def mpesa_payment(request):
    try:
        phone_number = request.POST.get("phone_number")
        amount = request.POST.get("amount")
        transaction_reference = request.POST.get("transaction_reference")

        # Ensure all required parameters are provided
        if not phone_number or not amount or not transaction_reference:
            return HttpResponse(
                json.dumps({"message": "Phone number, amount, and transaction reference are required."}),
                status=400,
            )

        # M-Pesa API URL for STK push
        mpesa_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        # Set headers for M-Pesa API request
        headers = {
            "Authorization": f"Bearer {settings.MPESA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        # Prepare the payload for the M-Pesa payment request
        payload = {
            "BusinessShortcode": settings.MPESA_SHORTCODE,
            "LipaNaMpesaOnlineShortcode": settings.MPESA_SHORTCODE,
            "LipaNaMpesaOnlineLipa": {
                "PhoneNumber": phone_number,
                "Amount": amount,
                "TransactionReference": transaction_reference,
            },
            "Shortcode": settings.MPESA_SHORTCODE,
            "CommandID": "CustomerPayBillOnline",
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "Amount": amount,
            "TransactionType": "Paybill",
            "CallBackURL": f"{settings.BASE_URL}/api/mpesa/callback/",
            "AccountReference": transaction_reference,
            "TransactionDesc": "Payment for goods/services",
        }

        # Make the request to M-Pesa API
        response = requests.post(mpesa_url, headers=headers, json=payload)

        # Handle M-Pesa API response
        if response.status_code == 200:
            response_data = response.json()
            return HttpResponse(
                json.dumps({
                    "message": "Payment request sent successfully.",
                    "data": response_data
                }),
                status=200
            )
        else:
            return HttpResponse(
                json.dumps({
                    "message": "Payment failed, please try again.",
                    "error": response.json()
                }),
                status=response.status_code
            )

    except Exception as e:
        return HttpResponse(
            json.dumps({"message": "Error processing M-Pesa payment.", "error": str(e)}),
            status=500,
        )