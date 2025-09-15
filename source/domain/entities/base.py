from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field, ConfigDict


class BaseEntity(BaseModel):
    id: Union[int, str, None] = None
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
