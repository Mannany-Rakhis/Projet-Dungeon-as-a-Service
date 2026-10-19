import logging

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.player import Player
from app.schemas.auth import PlayerCreate, TokenRead
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
) 

logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(message)


def register_player(player_data: PlayerCreate, session: Session) -> Player:
    player = Player(
        username=player_data.username,
        hashed_password=hash_password(player_data.password),
    )
    session.add(player)
    try:
        session.commit()
    except IntegrityError as error:
        # Annule la transaction avant de convertir le doublon en erreur métier.
        session.rollback()
        logger.warning("Inscription refusée : nom d'utilisateur déjà utilisé.")
        raise AuthServiceError(
            409,
            "USERNAME_TAKEN",
            "Ce nom d'utilisateur existe déjà.",
        ) from error
    session.refresh(player)
    logger.info("Compte joueur créé : %s", player.username)
    return player


def login_player(username: str, password: str, session: Session) -> TokenRead:
    player = session.exec(
        select(Player).where(Player.username == username)
    ).first()
    # Le même message évite de révéler si le compte ou le mot de passe est incorrect.
    if player is None or not verify_password(password, player.hashed_password):
        logger.warning("Échec de connexion pour le compte : %s", username)
        raise AuthServiceError(
            401,
            "INVALID_CREDENTIALS",
            "Nom d'utilisateur ou mot de passe incorrect.",
        )
    token = create_access_token(player.username)
    logger.info("Connexion réussie pour le compte : %s", player.username)
    return TokenRead(access_token=token)


def get_current_player(token: str, session: Session) -> Player:
    username = decode_access_token(token)
    if username is None:
        raise AuthServiceError(401, "INVALID_TOKEN", "Jeton invalide ou expiré.")

    player = session.exec(select(Player).where(Player.username == username)).first()
    if player is None:
        # Un jeton reste inutilisable si le compte associé n'existe plus.
        raise AuthServiceError(401, "INVALID_TOKEN", "Joueur introuvable.")
    return player
