# Stripe Integration

Stripe is a suite of payment APIs that powers commerce for online businesses of all sizes. It's designed to handle everything from accepting payments to managing subscriptions and sending payouts.

## Key Features

- **Payment Processing**: Accept credit cards, bank transfers, and other payment methods
- **Subscription Management**: Recurring billing with flexible pricing models
- **Invoicing**: Create and send professional invoices
- **Fraud Prevention**: Advanced tools to detect and prevent fraudulent transactions
- **Checkout Experience**: Customizable checkout flows for web and mobile
- **Global Support**: Accept payments in multiple currencies and payment methods

## Project Usage Patterns

In our project, Stripe is used for:

1. Processing one-time payments for premium features
2. Managing subscription tiers for recurring access
3. Handling payment success and cancellation flows
4. Storing payment method information securely

## Common Patterns

### Creating a Payment Intent

```python
import stripe
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/create-payment-intent")
async def create_payment(request: Request):
    data = await request.json()
    
    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=calculate_order_amount(data['items']),
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return {
            'clientSecret': intent['client_secret']
        }
    except Exception as e:
        return {"error": str(e)}
```

### Client-Side Implementation

```javascript
// Initialize Stripe.js
const stripe = Stripe('pk_test_your_key');
const elements = stripe.elements();

// Create payment form
const paymentElement = elements.create('payment');
paymentElement.mount('#payment-element');

// Handle form submission
const form = document.getElementById('payment-form');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  
  const {error} = await stripe.confirmPayment({
    elements,
    confirmParams: {
      return_url: 'https://example.com/success',
    },
  });

  if (error) {
    // Show error to your customer
    const messageContainer = document.querySelector('#error-message');
    messageContainer.textContent = error.message;
  }
});
```

### Creating a Subscription

```python
@router.post("/create-subscription")
async def create_subscription(request: Request):
    data = await request.json()
    
    try:
        # Create a customer
        customer = stripe.Customer.create(
            email=data['email'],
            payment_method=data['paymentMethodId'],
            invoice_settings={
                'default_payment_method': data['paymentMethodId'],
            },
        )
        
        # Create the subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {'price': data['priceId']},
            ],
            expand=['latest_invoice.payment_intent'],
        )
        
        return subscription
    except Exception as e:
        return {"error": str(e)}
```

### Handling Webhooks

```python
@router.post("/webhook")
async def webhook_received(request: Request):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    request_data = await request.body()
    
    if webhook_secret:
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request_data, sig_header=signature, secret=webhook_secret
            )
            event_data = event["data"]
        except Exception as e:
            return {"error": str(e)}
            
        # Handle the event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event_data["object"]
            # Handle successful payment
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event_data["object"]
            # Handle failed payment
            
    return {"status": "success"}
```

## Project-Specific Examples

From our project's `app/routers/payments.py`:

```python
@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Create a checkout session for the user
    # ...
```

## Documentation Links

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe.js Reference](https://stripe.com/docs/js)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)
- [Stripe Elements](https://stripe.com/docs/elements)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Python Library](https://stripe.com/docs/api/python)
