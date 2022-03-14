# kvom

the key-value store object mapping.

## Features

- key-value data mapping to Model
- support multiple k-v databases
- use `pydantic` to validate data

## Quick Start

first install `kvom` from pip:

```shell
python -m pip install -U kvom
```

then, define the model:

```python
from kvom import BaseModel, Source
from pydantic import EmailStr


class User(BaseModel):
    class Meta:
        source = Source("redis://localhost:6379/0")
        prefix = "custom_prefix"

    name: str
    age: int
    email: EmailStr


# save the model to database
user = User(name="chaojie", age=18, email="zhuzhezhe95@gmail.com")
user.save()
print(user.name)

# then, you can fetch it by key
User.get(user.key)

# or delete it
user.delete()
```
