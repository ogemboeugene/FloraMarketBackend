import base64
import datetime
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

        # Fetch M-Pesa configuration from environment variables
        consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        stk_push_url = os.getenv("MPESA_STK_PUSH_URL")
        callback_url = os.getenv("MPESA_CALLBACK_URL")
        auth_url = os.getenv("MPESA_AUTH_URL")

        # Step 1: Generate the access token
        auth_response = requests.get(auth_url, auth=(consumer_key, consumer_secret))
        if auth_response.status_code != 200:
            return HttpResponse(
                json.dumps({"message": "Failed to generate M-Pesa access token.", "error": auth_response.json()}),
                status=auth_response.status_code,
            )
        access_token = auth_response.json().get("access_token")

        # Step 2: Prepare STK push payload
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = f"{shortcode}{passkey}{timestamp}".encode("utf-8")
        encoded_password = base64.b64encode(password).decode("utf-8")

        payload = {
            "BusinessShortCode": shortcode,
            "Password": encoded_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": transaction_reference,
            "TransactionDesc": "Payment for goods/services",
        }

        # Step 3: Send the STK push request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(stk_push_url, headers=headers, json=payload)

        # Handle STK push response
        if response.status_code == 200:
            response_data = response.json()
            return HttpResponse(
                json.dumps({"message": "Payment request sent successfully.", "data": response_data}),
                status=200,
            )
        else:
            return HttpResponse(
                json.dumps({"message": "Payment failed, please try again.", "error": response.json()}),
                status=response.status_code,
            )

    except Exception as e:
        return HttpResponse(
            json.dumps({"message": "Error processing M-Pesa payment.", "error": str(e)}),
            status=500,
        )
