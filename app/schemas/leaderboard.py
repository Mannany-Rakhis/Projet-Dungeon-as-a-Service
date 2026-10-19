from pydantic import BaseModel


class LeaderboardRead(BaseModel):
    id: int
    nom: str
    classe: str
    victoire: bool
    or_: int

    model_config = {"from_attributes": True}
