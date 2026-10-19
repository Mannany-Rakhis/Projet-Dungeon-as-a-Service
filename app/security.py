import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

# La variable d'environnement permet d'utiliser une clé propre à chaque environnement.
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-only-change-this-secret-before-deployment",
)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# pwdlib choisit un algorithme de hachage adapté et génère un sel par mot de passe.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(username: str) -> str:
    # Les dates UTC et l'expiration limitent la durée de validité du jeton.
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": username, "exp": expires_at},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    # PyJWT vérifie la signature et l'expiration avant de lire l'identifiant du joueur.
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None

    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
