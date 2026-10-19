from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    """Données validées nécessaires à la création d'un compte joueur."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class PlayerRead(BaseModel):
    """Informations publiques du joueur, sans son mot de passe haché."""

    id: int
    username: str


class TokenRead(BaseModel):
    """Jeton d'accès au format attendu par l'authentification Bearer."""

    access_token: str
    token_type: str = "bearer"
