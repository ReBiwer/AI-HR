from pydantic import BaseModel


class TGUser(BaseModel):
    hh_id: str
    name: str
    mid_name: str
