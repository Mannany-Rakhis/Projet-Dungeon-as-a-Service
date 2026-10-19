from collections.abc import Awaitable, Callable
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.hero import Hero
from app.models.player import Player
from app.routes.auth import get_current_player
from app.schemas.dungeon import CombatRead, HeroMove, RoomRead
from app.schemas.hero import HeroCreate, HeroRead
from app.services.hero_service import (
    HeroServiceError,
    attack_with_hero as service_attack,
    create_hero as service_create,
    get_hero as service_get,
    get_hero_room as service_get_room,
    list_heroes as service_list,
    move_hero as service_move,
    rest_hero as service_rest,
)

router = APIRouter(prefix="/heroes", tags=["Héros"])
CurrentPlayer = Annotated[Player, Depends(get_current_player)]
Result = TypeVar("Result")


@router.post("", response_model=HeroRead, status_code=status.HTTP_201_CREATED)
def create_hero(
    hero_data: HeroCreate,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> Hero:
    """Crée un héros pour le joueur authentifié."""
    return _call_service(service_create, hero_data, player, session)


@router.get("", response_model=list[HeroRead])
def list_heroes(
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> list[Hero]:
    """Liste les héros du joueur authentifié."""
    return list(_call_service(service_list, player, session))


@router.get("/{hero_id}", response_model=HeroRead)
def get_hero(
    hero_id: int,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> Hero:
    """Retourne un héros appartenant au joueur authentifié."""
    return _call_service(service_get, hero_id, player, session)


@router.get("/{hero_id}/room", response_model=RoomRead)
def get_hero_room(
    hero_id: int,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> RoomRead:
    """Retourne la salle actuelle du héros."""
    return _call_service(service_get_room, hero_id, player, session)


@router.post("/{hero_id}/move", response_model=RoomRead)
def move_hero(
    hero_id: int,
    move: HeroMove,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> RoomRead:
    """Déplace le héros ; les actions refusées par les règles métier renvoient 409."""
    return _call_service(service_move, hero_id, move, player, session)


@router.post("/{hero_id}/attack", response_model=CombatRead)
def attack_with_hero(
    hero_id: int,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> CombatRead:
    """Résout un tour : le héros frappe d'abord, le monstre riposte s'il survit.

    Renvoie 409 si le héros est mort ou si aucun combat n'est en cours.
    """
    return _call_service(service_attack, hero_id, player, session)


@router.post("/{hero_id}/rest", response_model=HeroRead)
async def rest_hero(
    hero_id: int,
    player: CurrentPlayer,
    session: Session = Depends(get_session),
) -> Hero:
    """Repose le héros de façon asynchrone en attendant trois secondes.

    Renvoie 409 si le héros est mort ou s'il est en combat.
    """
    return await _call_async_service(service_rest, hero_id, player, session)


def _http_error(error: HeroServiceError) -> HTTPException:
    """Convertit une erreur métier en réponse HTTP structurée."""
    return HTTPException(
        status_code=error.status_code,
        detail={"error": error.error, "message": error.message},
    )


def _call_service(operation: Callable[..., Result], *args: object) -> Result:
    """Centralise la traduction des erreurs métier pour les routes synchrones."""
    try:
        return operation(*args)
    except HeroServiceError as error:
        raise _http_error(error) from error


async def _call_async_service(
    operation: Callable[..., Awaitable[Result]],
    *args: object,
) -> Result:
    """Même traduction que _call_service, en attendant un service asynchrone."""
    try:
        return await operation(*args)
    except HeroServiceError as error:
        raise _http_error(error) from error
