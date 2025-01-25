import base64
import datetime
import json
import os
import requests
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv

load_dotenv() 
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


# Load environment variables
consumer_key = os.environ.get("MPESA_CONSUMER_KEY")
consumer_secret = os.environ.get("MPESA_CONSUMER_SECRET")
shortcode = os.environ.get("SHORTCODE")
passkey = os.environ.get("MPESA_PASSKEY")
stk_push_url = os.environ.get("MPESA_STK_PUSH_URL")
auth_url = os.environ.get("MPESA_AUTH_URL")
callback_url = os.environ.get("MPESA_CALLBACK_URL")


@require_http_methods(["POST"])
@csrf_exempt
def mpesa_payment(request):
    try:
        data = json.loads(request.body)

        phone_number = data.get("phoneNumber")
        amount = data.get("amount")
        transaction_reference = data.get("transactionReference")

        if not phone_number or not amount:
            return HttpResponse(
                json.dumps({"message": "Phone number and amount are required."}),
                status=400,
                content_type="application/json",
            )

        auth_response = requests.get(auth_url, auth=(consumer_key, consumer_secret))

        if auth_response.status_code != 200:
            return HttpResponse(
                json.dumps({"message": "Failed to generate M-Pesa access token.", "error": auth_response.json()}),
                status=auth_response.status_code,
                content_type="application/json",
            )
        
        access_token = auth_response.json().get("access_token")
        if not access_token:
            return HttpResponse(
                json.dumps({"message": "No access token received from M-Pesa."}),
                status=500,
                content_type="application/json",
            )

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
            "AccountReference": transaction_reference or "DefaultReference",
            "TransactionDesc": "Payment for goods/services",
        }
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
                content_type="application/json",
            )
        else:
            error_message = response.json() if response.status_code != 200 else "Payment failed, please try again."
            return HttpResponse(
                json.dumps({"message": error_message, "error": response.json()}),
                status=response.status_code,
                content_type="application/json",
            )

    except requests.exceptions.RequestException as e:
        return HttpResponse(
            json.dumps({"message": "Network or request error occurred.", "error": str(e)}),
            status=500,
            content_type="application/json",
        )
    
    except Exception as e:
        import traceback
        return HttpResponse(
            json.dumps({"message": "Error processing M-Pesa payment.", "error": str(e)}),
            status=500,
            content_type="application/json",
        )