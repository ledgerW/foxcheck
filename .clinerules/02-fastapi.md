# FastAPI Framework

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.

## Key Features

- **Fast**: Very high performance, on par with NodeJS and Go
- **Fast to code**: Increase developer productivity by ~200-300%
- **Fewer bugs**: Reduce about 40% of human-induced errors
- **Intuitive**: Great editor support with auto-completion
- **Easy**: Designed to be easy to use and learn
- **Short**: Minimize code duplication
- **Robust**: Get production-ready code with automatic interactive documentation
- **Standards-based**: Based on (and fully compatible with) the open standards for APIs: OpenAPI and JSON Schema

## Project Usage Patterns

In our project, FastAPI is used for:

1. Creating API endpoints in the `app/routers/` directory
2. Handling form submissions and user authentication
3. Serving web pages with Jinja2 templates
4. Managing payment processing with Stripe integration

## Common Patterns

### Router Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]

@router.get("/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
```

### Dependency Injection

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items/")
async def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items
```

### Request Body Validation

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@router.post("/items/")
async def create_item(item: Item):
    return item
```

### Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    return user
```

## Project-Specific Examples

From our project's routers:

```python
@router.post("/generate")
async def generate_results(
    request: Request,
    form_data: dict,
    current_user: User = Depends(get_current_user)
):
    # Process AI generation request
    # ...
```

```python
@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Handle user login
    # ...
```

## Documentation Links

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [FastAPI GitHub Repository](https://github.com/tiangolo/fastapi)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Starlette Documentation](https://www.starlette.io/)
- [SQLAlchemy with FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
