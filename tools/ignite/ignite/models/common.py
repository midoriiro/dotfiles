from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

IdentifierPattern = "([a-zA-Z0-9]|[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9])"

Identifier = Annotated[
    str, 
    StringConstraints(
        min_length=1,
        max_length=256,
        pattern=rf"^{IdentifierPattern}$"
    )
]
