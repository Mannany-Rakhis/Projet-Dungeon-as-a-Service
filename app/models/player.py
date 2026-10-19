from sqlmodel import Field, SQLModel


class Player(SQLModel, table=True):
    """Compte joueur persisté en base pour l'authentification."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    # Seul le hash du mot de passe est stocké, jamais le mot de passe lui-même.
    hashed_password: str
