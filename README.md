# ecommerce-backend
Django backend for eCommerce project

This project is built using Django REST Framework to provide the backend API for eCommerce project. The frontend is available [here](https://github.com/kkosiba/ecommerce-frontend). 

Features
--------
1. Products API endpoint available at `/api/products/`.
2. Custom user authentication using JSON Web Tokens. The API is available at `/api/accounts/`.
2. Simple newsletter functionality: superuser can view the list of all subscribers in Django admin panel; any visitor can subscribe. The relevant API endpoint is available at `/api/newsletter/`.
3. [Stripe](https://stripe.com/) payments API endpoint available at `/api/payments/`.

Main requirements
------------

1. `python` 3.7, 3.8, 3.9, 3.10
2. `Django` >=3.2,<4
3. `PostgreSQL` 11.1

This project also uses other packages (see `requirements.txt` file for details).
For instance, tag support is provided by [django-taggit](https://github.com/alex/django-taggit) and image processing is thanks to [Pillow](https://github.com/python-pillow/Pillow).

## How to set up

### Setup using Docker

The easiest way to get backend up and running is via [Docker](https://www.docker.com/). See [docs](https://docs.docker.com/get-started/) to get started. Once set up run the following command:

`docker-compose up`

This command takes care of populating products list with sample data.

It may take a while for the process to complete, as Docker needs to pull required dependencies. Once it is done, the application should be accessible at `0.0.0.0:8000`.

### Manual setup

Firstly, create a new directory and change to it:

`mkdir ecommerce-backend && cd ecommerce-backend`

Then, clone this repository to the current directory:

`git clone https://github.com/kkosiba/ecommerce-backend.git .`

For the backend to work, one needs to setup database like SQLite or PostgreSQL on a local machine. This project uses PostgreSQL by default (see [Django documentation](https://docs.djangoproject.com/en/3.2/ref/settings/#databases).

The database settings are specified in `src/settings/local.py`. In particular the default database name is `eCommerceDjango`, which can be created from the PostgreSQL shell by running `createdb eCommerceDjango`.

Next, set up a virtual environment and activate it:

`python3 -m venv env && source env/bin/activate`

Install required packages:
`cd requirements.txt`
for testing locally
`pip install -r base.txt`
`pip install -r development.txt`

production you will use
`pip install -r base.txt`
`pip install -r production.txt`

Next, perform migration:

`python manage.py migrate --settings=src.settings.local`

At this point, one may want to create a superuser account and create some products. One can also use sample data provided in `products/fixtures.json` by running:

`python manage.py loaddata products/fixture.json --settings=src.settings.local`

The backend is now ready. Run a local server with

`python manage.py runserver --settings=src.settings.local`

The backend should be available at `localhost:8000`.

In order to use [Stripe payments](https://stripe.com/) one needs to create an account and obtain a pair of keys (available in the dashboard after signing in). 
create a environment file .env and have provide your fields correctly

# Stripe Configuration
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>

# M-Pesa Configuration
MPESA_ACCESS_TOKEN=<your-mpesa-access-token>
MPESA_SHORTCODE=<your-mpesa-shortcode>
MPESA_SHORTCODE_KEY=<your-mpesa-shortcode-key>
MPESA_SHORTCODE_LIPA=<your-mpesa-lipa-shortcode>
MPESA_BASE_URL=https://api.safaricom.co.ke
MPESA_LIPA_URL=https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest
MPESA_CALL_BACK_URL=<your-mpesa-callback-url>