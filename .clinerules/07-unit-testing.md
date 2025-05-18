# Unit Testing Approach

This document outlines our comprehensive approach to unit testing in Python applications, with a specific focus on testing FastAPI applications that integrate with external services like Stytch, Stripe, and LLM providers.

## Core Testing Principles

1. **Test Isolation**: Each test should be independent and not rely on the state from other tests.
2. **Deterministic Results**: Tests should produce the same results regardless of when or where they're run.
3. **Fast Execution**: Unit tests should execute quickly to enable rapid feedback during development.
4. **Comprehensive Coverage**: Tests should cover both happy paths and error cases.
5. **Clean Up**: Always clean up test data after tests to prevent test pollution.

## Testing Structure

We organize our tests into a clear hierarchy:

```
tests/
├── conftest.py                  # Shared fixtures and test configuration
├── unit/                        # Unit tests for individual components
│   ├── models/                  # Tests for database models
│   ├── routers/                 # Tests for API endpoints
│   └── utils/                   # Tests for utility functions
```

## Database Testing

### In-Memory SQLite for Testing

We use an in-memory SQLite database for testing to ensure:
- Tests run quickly
- No persistence between test runs
- No impact on development or production databases

```python
@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database engine for testing."""
    # Use in-memory SQLite database with shared cache for testing
    TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared"
    
    # Create a test engine with StaticPool to maintain a single connection
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    SQLModel.metadata.create_all(test_engine)
    
    # Return the engine
    yield test_engine
    
    # Drop all tables after tests
    SQLModel.metadata.drop_all(test_engine)
    
    # Explicitly close connections and dispose of the engine
    test_engine.dispose()
```

### Session Management

We create a session fixture that depends on the engine:

```python
@pytest.fixture
def test_db(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    with Session(test_db_engine) as session:
        yield session
```

### Dependency Overrides

For FastAPI applications, we override the database dependency:

```python
@pytest.fixture
def client(test_db_engine) -> TestClient:
    """Create a test client with a test database session."""
    # Override the get_session dependency to use our test database
    def override_get_session():
        with Session(test_db_engine) as session:
            yield session
    
    # Override the dependency in the app
    app.dependency_overrides[get_session] = override_get_session
    
    # Create and return a test client
    with TestClient(app) as client:
        yield client
    
    # Remove the override after the test
    app.dependency_overrides.clear()
```

## Mocking External Services

### Mocking Stytch Authentication

Stytch is an authentication service that provides email magic links, OAuth, and session management. We mock it using pytest-mock:

```python
@pytest.fixture
def mock_stytch_client(mocker: MockerFixture):
    """Mock the Stytch client."""
    mock_client = mocker.patch("clients.get_stytch_client")
    
    # Create a mock client with the necessary methods
    mock_client_instance = mocker.MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the magic links methods
    mock_client_instance.magic_links = mocker.MagicMock()
    mock_client_instance.magic_links.email = mocker.MagicMock()
    mock_client_instance.magic_links.email.login_or_create = mocker.MagicMock()
    mock_client_instance.magic_links.authenticate = mocker.MagicMock()
    
    # Mock the sessions methods
    mock_client_instance.sessions = mocker.MagicMock()
    mock_client_instance.sessions.authenticate = mocker.MagicMock()
    mock_client_instance.sessions.authenticate_jwt = mocker.MagicMock()
    
    return mock_client_instance
```

#### Mocking Stytch Errors

For testing error handling, we create a helper function to generate properly structured Stytch errors:

```python
def create_mock_stytch_error(message, status_code, error_type, error_message, request_id):
    """Create a properly structured mock StytchError."""
    from stytch.core.response_base import StytchError
    
    # Create the error object
    mock_error = StytchError(message)
    mock_error.status_code = status_code
    mock_error.error_type = error_type
    mock_error.error_message = error_message
    mock_error.request_id = request_id
    
    # Add details attribute with original_json
    from unittest.mock import MagicMock
    mock_error.details = MagicMock()
    mock_error.details.original_json = {"error": error_message}
    
    return mock_error
```

#### Example: Testing Authentication Flow

```python
def test_login_success(client, mock_stytch_client):
    # Configure the mock to return a successful response
    mock_stytch_client.magic_links.email.login_or_create.return_value = {
        "status_code": 200,
        "request_id": "request-id-123",
        "email_id": "email-id-123"
    }
    
    # Make the request
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com"}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "success" in response.json()
    assert response.json()["success"] is True
    
    # Verify the mock was called correctly
    mock_stytch_client.magic_links.email.login_or_create.assert_called_once_with(
        email="test@example.com",
        login_magic_link_url="https://example.com/authenticate",
        signup_magic_link_url="https://example.com/authenticate"
    )
```

### Mocking Stripe Payments

Stripe is a payment processing service. We mock it comprehensively to test payment flows:

```python
@pytest.fixture
def mock_stripe(mocker: MockerFixture):
    """Mock the Stripe client."""
    # Mock the stripe module in clients.py
    mock_stripe = mocker.patch("clients.stripe")
    
    # Mock the checkout.Session methods
    mock_stripe.checkout = mocker.MagicMock()
    mock_stripe.checkout.Session = mocker.MagicMock()
    mock_stripe.checkout.Session.create = mocker.MagicMock()
    mock_stripe.checkout.Session.retrieve = mocker.MagicMock()
    
    # Mock the Subscription methods
    mock_stripe.Subscription = mocker.MagicMock()
    mock_stripe.Subscription.create = mocker.MagicMock()
    mock_stripe.Subscription.retrieve = mocker.MagicMock()
    mock_stripe.Subscription.modify = mocker.MagicMock()
    
    # Mock the PaymentIntent methods
    mock_stripe.PaymentIntent = mocker.MagicMock()
    mock_stripe.PaymentIntent.create = mocker.MagicMock()
    mock_stripe.PaymentIntent.retrieve = mocker.MagicMock()
    
    # Mock the Webhook methods
    mock_stripe.Webhook = mocker.MagicMock()
    mock_stripe.Webhook.construct_event = mocker.MagicMock()
    
    # Also patch any direct imports of stripe in payment modules
    mocker.patch("app.routers.payments.payment_checkout.stripe", mock_stripe)
    mocker.patch("app.routers.payments.payment_verification.stripe", mock_stripe)
    mocker.patch("app.routers.payments.payment_webhooks.stripe", mock_stripe)
    
    return mock_stripe
```

#### Example: Testing Checkout Session Creation

```python
def test_create_checkout_session(client, mock_stripe, mock_authenticated_user):
    # Configure the mock to return a successful response
    mock_stripe.checkout.Session.create.return_value = {
        "id": "cs_test_123",
        "url": "https://checkout.stripe.com/pay/cs_test_123"
    }
    
    # Make the request
    response = client.post(
        "/api/payments/create-checkout-session",
        json={"tier": "premium"}
    )
    
    # Check the response
    assert response.status_code == 200
    assert "checkout_url" in response.json()
    assert response.json()["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"
    
    # Verify the mock was called correctly
    mock_stripe.checkout.Session.create.assert_called_once()
    # Check specific parameters as needed
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert call_kwargs["payment_method_types"] == ["card"]
    assert call_kwargs["mode"] == "payment"
```

#### Example: Testing Webhook Handling

```python
def test_stripe_webhook_payment_succeeded(client, mock_stripe, test_db, test_user_in_db):
    # Configure the mock to return a constructed event
    event_data = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer": "cus_test_123",
                "payment_status": "paid",
                "metadata": {
                    "user_id": str(test_user_in_db.id),
                    "tier": "premium"
                }
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = event_data
    
    # Make the request
    response = client.post(
        "/api/payments/webhook",
        headers={"Stripe-Signature": "test_signature"},
        json=event_data
    )
    
    # Check the response
    assert response.status_code == 200
    
    # Verify the user's payment tier was updated
    updated_user = test_db.get(User, test_user_in_db.id)
    assert updated_user.payment_tier == "premium"
```

### Mocking LLM Calls (LangChain/OpenAI)

For AI-powered applications, we mock LLM calls to ensure deterministic test results:

```python
@pytest.fixture
def mock_langchain_llm(mocker: MockerFixture):
    """Mock the LangChain LLM."""
    # Mock the ChatOpenAI class
    mock_llm = mocker.patch("app.routers.ai.ai_generation.llm")
    
    # Create a mock for the structured output method
    mock_structured_output = mocker.MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_output
    
    # Create a mock for the invoke method
    mock_structured_output.invoke = mocker.MagicMock()
    
    return mock_llm
```

#### Creating Mock LLM Outputs

We create fixtures for standard LLM outputs to ensure consistency:

```python
@pytest.fixture
def mock_summary_output():
    """Create a mock SummaryOutput."""
    return SummaryOutput(
        mantra="Test mantra for a purposeful life",
        purpose="This is a test purpose summary that provides guidance and direction."
    )

@pytest.fixture
def mock_full_plan_output():
    """Create a mock FullPlanOutput."""
    return FullPlanOutput(
        mantra="Test mantra for a purposeful life",
        purpose="This is a test purpose summary that provides guidance and direction.",
        next_steps={
            "today": [
                {"text": "Reflect on your values", "category": "reflection"}
            ],
            "next_7_days": [
                {"text": "Start a daily meditation practice", "category": "mindfulness"}
            ],
            "next_30_days": [
                {"text": "Take a course related to your interests", "category": "learning"}
            ],
            "next_180_days": [
                {"text": "Start a meaningful project", "category": "creativity"}
            ]
        },
        daily_plan={
            "weekdays": {
                "morning": [
                    {"text": "Meditate for 10 minutes", "category": "mindfulness"}
                ],
                "afternoon": [
                    {"text": "Take a short walk", "category": "health"}
                ],
                "evening": [
                    {"text": "Reflect on the day", "category": "reflection"}
                ]
            },
            "weekends": {
                "morning": [
                    {"text": "Extended meditation session", "category": "mindfulness"}
                ],
                "afternoon": [
                    {"text": "Spend time in nature", "category": "nature"}
                ],
                "evening": [
                    {"text": "Plan for the week ahead", "category": "planning"}
                ]
            }
        },
        obstacles=[
            {
                "challenge": "Self-doubt and fear of failure",
                "solution": "Practice self-compassion",
                "type": "personal"
            }
        ]
    )
```

#### Example: Testing AI Generation

```python
@pytest.mark.asyncio
async def test_generate_purpose(mock_langchain_llm, mock_summary_output, test_user, test_form_responses):
    """Test generating purpose content."""
    # Mock the LangChain LLM to return the mock summary output
    mock_langchain_llm.with_structured_output.return_value.invoke.return_value = mock_summary_output
    
    # Mock the zodiac info
    zodiac_info = {
        "sign": "Libra",
        "element": "Air",
        "traits": "Balanced, fair, social"
    }
    
    # Call the function
    result = generate_purpose(test_user, zodiac_info, test_form_responses)
    
    # Check the result
    assert result == mock_summary_output
    assert result.mantra == mock_summary_output.mantra
    assert result.purpose == mock_summary_output.purpose
    
    # Verify LangChain was called correctly
    mock_langchain_llm.with_structured_output.assert_called_once_with(SummaryOutput)
    mock_langchain_llm.with_structured_output.return_value.invoke.assert_called_once()
```

## Testing FastAPI Endpoints

### Setting Up the Test Client

```python
@pytest.fixture
def client(test_db_engine) -> TestClient:
    """Create a test client with a test database session."""
    # Override the get_session dependency
    def override_get_session():
        with Session(test_db_engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

### Mocking Authentication for Protected Routes

```python
@pytest.fixture
def mock_authenticated_user(mocker: MockerFixture):
    """Mock the authenticated user."""
    # Create a mock user object
    mock_user = mocker.MagicMock()
    mock_user.user_id = str(uuid.uuid4())
    mock_user.emails = [mocker.MagicMock(email="test@example.com")]
    
    # Mock the get_authenticated_user function
    mocker.patch("app.routers.auth.get_authenticated_user", return_value=mock_user)
    
    return mock_user
```

### Example: Testing a Protected Endpoint

```python
def test_protected_endpoint(client, mock_authenticated_user, test_db, test_user_in_db):
    # Make the request
    response = client.get(f"/api/users/{test_user_in_db.id}/profile")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == test_user_in_db.name
    assert response.json()["email"] == test_user_in_db.email
```

## Best Practices

### 1. Test Data Cleanup

Always clean up test data after tests to prevent test pollution:

```python
@pytest.fixture
def test_user_in_db(test_db, test_user) -> User:
    """Add a test user to the database and return it."""
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)
    yield test_user
    
    # Clean up after the test
    test_db.delete(test_user)
    test_db.commit()
```

### 2. Descriptive Test Names

Use descriptive test names that explain what is being tested:

```python
def test_login_with_invalid_email_format_returns_400():
    # Test implementation
    pass

def test_premium_content_requires_payment_tier():
    # Test implementation
    pass
```

### 3. Test Both Happy Paths and Error Cases

```python
def test_user_registration_success():
    # Test successful registration
    pass

def test_user_registration_with_existing_email_fails():
    # Test registration with an email that already exists
    pass
```

### 4. Use Parametrized Tests for Multiple Similar Cases

```python
@pytest.mark.parametrize(
    "email,expected_status",
    [
        ("valid@example.com", 200),
        ("invalid-email", 400),
        ("", 400),
        (None, 422),  # FastAPI validation error
    ]
)
def test_login_with_various_emails(client, email, expected_status):
    response = client.post("/api/auth/login", json={"email": email})
    assert response.status_code == expected_status
```

### 5. Test Database Transactions

Ensure database transactions are properly committed or rolled back:

```python
def test_database_transaction_commit(test_db):
    # Create a new user
    user = User(name="Test User", email="test@example.com")
    test_db.add(user)
    test_db.commit()
    
    # Verify the user was added
    retrieved_user = test_db.exec(select(User).where(User.email == "test@example.com")).first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"
    
    # Clean up
    test_db.delete(retrieved_user)
    test_db.commit()
```

### 6. Mock External API Calls

Never make real API calls in tests:

```python
def test_external_api_call(mocker):
    # Mock the requests library
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    
    mocker.patch("requests.get", return_value=mock_response)
    
    # Call the function that makes the API call
    result = get_external_data()
    
    # Verify the result
    assert result == {"data": "test"}
```

## Running Tests

### Basic Test Run

```bash
poetry run pytest
```

### Running with Coverage

```bash
poetry run pytest --cov=app
```

### Running Specific Tests

```bash
# Run tests in a specific file
poetry run pytest tests/unit/models/test_user_model.py

# Run tests in a specific directory
poetry run pytest tests/unit/routers/

# Run tests matching a pattern
poetry run pytest -k "login or registration"
```

### Debugging Tests

```bash
# Show print statements
poetry run pytest -v

# Show detailed output
poetry run pytest -vv

# Stop on first failure
poetry run pytest -x

# Enter PDB on failure
poetry run pytest --pdb
```

## Conclusion

This comprehensive testing approach ensures our applications are thoroughly tested, with a focus on isolation, determinism, and comprehensive coverage. By properly mocking external services like Stytch, Stripe, and LLM providers, we can test our application's behavior without relying on external services, making our tests faster, more reliable, and more predictable.
