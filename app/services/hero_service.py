import asyncio
import logging
from collections.abc import Sequence

from sqlmodel import Session, select

from app.domain.heroes import creer_heros
from app.models.hero import Hero
from app.models.player import Player
from app.schemas.dungeon import CombatRead, HeroMove, MonsterRead, RoomRead
from app.schemas.hero import HeroCreate
from app.services.dungeon_map import (
    FINAL_ROOM,
    START_ROOM,
    get_monster,
    get_room as get_dungeon_room,
)

logger = logging.getLogger(__name__)


class HeroServiceError(Exception):
    """Erreur de règle métier traduite en réponse HTTP par les routes."""

    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(message)


def create_hero(hero_data: HeroCreate, player: Player, session: Session) -> Hero:
    hero_domain = creer_heros(
        hero_data.classe,
        hero_data.force,
        hero_data.agilite,
        hero_data.intelligence,
    )
    hero = Hero(
        **hero_data.model_dump(),
        pv=hero_domain.pv_max,
        pv_max=hero_domain.pv_max,
        salle_actuelle=START_ROOM,
        owner_id=player.id,
    )
    session.add(hero)
    session.commit()
    session.refresh(hero)
    logger.info(
        "Création du héros id=%s joueur=%s nom=%s",
        hero.id,
        player.id,
        hero.nom,
    )
    return hero


def list_heroes(player: Player, session: Session) -> Sequence[Hero]:
    return session.exec(select(Hero).where(Hero.owner_id == player.id)).all()


def get_hero(hero_id: int, player: Player, session: Session) -> Hero:
    return _get_owned_hero(hero_id, player, session)


def get_hero_room(hero_id: int, player: Player, session: Session) -> RoomRead:
    hero = _get_owned_hero(hero_id, player, session)
    return _room_read_for_hero(hero)


def move_hero(
    hero_id: int,
    move: HeroMove,
    player: Player,
    session: Session,
) -> RoomRead:
    """Déplace un héros vivant hors combat ; renvoie 409 s'il est mort/en combat."""
    hero = _get_owned_hero(hero_id, player, session)
    _ensure_hero_alive(hero)
    if hero.en_combat:
        raise HeroServiceError(
            409,
            "IN_COMBAT",
            "Vous ne pouvez pas vous déplacer pendant un combat.",
        )

    current_room = get_dungeon_room(hero.salle_actuelle)
    if current_room is None:
        raise HeroServiceError(
            500,
            "INVALID_HERO_ROOM",
            "La salle actuelle du héros est absente de la carte.",
        )

    next_room_id = current_room["exits"].get(move.direction)
    if next_room_id is None:
        raise HeroServiceError(
            400,
            "NO_EXIT",
            f"Il n'y a pas de passage vers le {move.direction}.",
        )

    next_room = get_dungeon_room(next_room_id)
    if next_room is None:
        raise HeroServiceError(
            500,
            "INVALID_DESTINATION",
            "La salle de destination est absente de la carte.",
        )

    monster_id = next_room["monster"]
    monster_data = get_monster(monster_id) if monster_id is not None else None
    if monster_id is not None and monster_data is None:
        raise HeroServiceError(
            500,
            "INVALID_MONSTER",
            "Le monstre de la salle de destination est absent de la carte.",
        )

    previous_room_id = hero.salle_actuelle
    hero.salle_actuelle = next_room_id
    hero.monstre_pv = monster_data["hp"] if monster_data is not None else None
    session.add(hero)
    session.commit()
    session.refresh(hero)
    logger.info(
        "Déplacement du héros id=%s salle=%s destination=%s",
        hero.id,
        previous_room_id,
        next_room_id,
    )
    return _room_read_for_hero(hero)


def attack_with_hero(hero_id: int, player: Player, session: Session) -> CombatRead:
    """Joue un tour : le héros frappe d'abord, puis le monstre riposte s'il survit.

    Renvoie 409 si le héros est mort ou si aucun combat n'est en cours.
    """
    hero = _get_owned_hero(hero_id, player, session)
    _ensure_hero_alive(hero)
    if not hero.en_combat:
        raise HeroServiceError(
            409, "NO_MONSTER", "Aucun monstre à combattre dans cette salle."
        )

    current_room = get_dungeon_room(hero.salle_actuelle)
    monster_id = current_room["monster"] if current_room is not None else None
    monster_hp = hero.monstre_pv
    if monster_id is None or monster_hp is None:
        raise HeroServiceError(
            409, "NO_MONSTER", "Aucun monstre à combattre dans cette salle."
        )

    monster_data = get_monster(monster_id)
    if monster_data is None:
        raise HeroServiceError(
            500,
            "INVALID_MONSTER",
            "Le monstre du combat actuel est absent de la carte.",
        )

    hero_domain = creer_heros(
        hero.classe,
        hero.force,
        hero.agilite,
        hero.intelligence,
    )
    damage_dealt, critical = hero_domain.calculer_degats()
    monster_hp = max(0, monster_hp - damage_dealt)
    damage_taken = 0
    gold_earned = 0
    victory = False

    if monster_hp == 0:
        issue = "monstre_vaincu"
        gold_earned = monster_data["gold"]
        final_room = get_dungeon_room(FINAL_ROOM)
        victory = final_room is not None and final_room["monster"] == monster_id
        hero.monstre_pv = None
        hero.victoire = hero.victoire or victory
    else:
        damage_taken = hero_domain.subir_degats(monster_data["attack"])
        hero.pv = max(0, hero.pv - damage_taken)
        hero.monstre_pv = monster_hp
        issue = "heros_mort" if not hero.est_vivant else "en_cours"

    hero.or_ += gold_earned
    session.add(hero)
    session.commit()
    session.refresh(hero)
    logger.info(
        "Attaque du héros id=%s monstre=%s dégâts_infligés=%s "
        "dégâts_subis=%s pv_héros=%s pv_monstre=%s",
        hero.id,
        monster_id,
        damage_dealt,
        damage_taken,
        hero.pv,
        monster_hp,
    )
    if issue == "heros_mort":
        logger.warning(
            "Mort du héros id=%s pendant le combat contre %s",
            hero.id,
            monster_id,
        )
    if victory:
        logger.info("Victoire du héros id=%s dans la salle finale", hero.id)

    return CombatRead(
        degats_infliges=damage_dealt,
        critique=critical,
        degats_subis=damage_taken,
        pv_heros=hero.pv,
        pv_monstre=monster_hp,
        issue=issue,
        or_gagne=gold_earned,
        victoire=victory,
    )


async def rest_hero(hero_id: int, player: Player, session: Session) -> Hero:
    """Attend ``asyncio.sleep(3)`` puis restaure les PV, uniquement hors combat.

    Renvoie 409 si le héros est mort ou s'il est en combat.
    """
    hero = _get_owned_hero(hero_id, player, session)
    _ensure_hero_alive(hero)
    if hero.en_combat:
        raise HeroServiceError(
            409,
            "IN_COMBAT",
            "Vous ne pouvez pas vous reposer pendant un combat.",
        )

    await asyncio.sleep(3)
    hero.pv = hero.pv_max
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


def _get_owned_hero(hero_id: int, player: Player, session: Session) -> Hero:
    hero = session.get(Hero, hero_id)
    if hero is None:
        raise HeroServiceError(
            404,
            "HERO_NOT_FOUND",
            f"Héros avec l'identifiant {hero_id} introuvable.",
        )
    if hero.owner_id != player.id:
        raise HeroServiceError(
            403,
            "NOT_YOUR_HERO",
            "Ce héros appartient à un autre joueur.",
        )
    return hero


def _ensure_hero_alive(hero: Hero) -> None:
    """Refuse les actions d'un héros mort avec une erreur HTTP 409."""
    if not hero.est_vivant:
        raise HeroServiceError(409, "HERO_DEAD", "Un héros mort ne peut pas agir.")


def _room_read_for_hero(hero: Hero) -> RoomRead:
    room = get_dungeon_room(hero.salle_actuelle)
    if room is None:
        raise HeroServiceError(
            500,
            "INVALID_HERO_ROOM",
            "La salle actuelle du héros est absente de la carte.",
        )

    monster = None
    monster_id = room["monster"] if hero.en_combat else None
    if hero.en_combat and monster_id is None:
        raise HeroServiceError(
            500,
            "INVALID_HERO_COMBAT",
            "Un combat est enregistré dans une salle sans monstre.",
        )
    if monster_id is not None and hero.monstre_pv is not None:
        monster_data = get_monster(monster_id)
        if monster_data is None:
            raise HeroServiceError(
                500,
                "INVALID_MONSTER",
                "Le monstre du combat actuel est absent de la carte.",
            )
        monster = MonsterRead(
            id=monster_id,
            name=monster_data["name"],
            hp=hero.monstre_pv,
            attack=monster_data["attack"],
            gold=monster_data["gold"],
        )
    return RoomRead(
        id=hero.salle_actuelle,
        name=room["name"],
        description=room["description"],
        exits=room["exits"],
        monster=monster,
    )
