import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.models.hero import Hero
from app.models.player import Player  # noqa: F401
from app.routes.leaderboard import router


@pytest.fixture
def leaderboard_client(tmp_path):
    engine = create_engine(
        URL.create("sqlite", database=str(tmp_path / "leaderboard.db")),
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_session] = get_test_session

    with TestClient(test_app) as client:
        yield client, engine

    engine.dispose()


def make_hero(
    nom: str,
    *,
    victoire: bool = False,
    or_: int = 0,
) -> Hero:
    return Hero(
        nom=nom,
        classe="guerrier",
        force=6,
        agilite=2,
        intelligence=2,
        salle_actuelle="start",
        victoire=victoire,
        or_=or_,
    )


def test_empty_leaderboard_is_public_and_returns_empty_list(leaderboard_client) -> None:
    client, _engine = leaderboard_client

    response = client.get("/leaderboard")

    assert response.status_code == 200
    assert response.json() == []


def test_leaderboard_sorts_winners_first_then_by_gold(leaderboard_client) -> None:
    client, engine = leaderboard_client
    with Session(engine) as session:
        session.add_all(
            [
                make_hero("Non-vainqueur riche", or_=1000),
                make_hero("Vainqueur faible", victoire=True, or_=10),
                make_hero("Vainqueur riche", victoire=True, or_=100),
                make_hero("Vainqueur moyen", victoire=True, or_=50),
            ]
        )
        session.commit()

    response = client.get("/leaderboard")

    assert response.status_code == 200
    assert [entry["nom"] for entry in response.json()] == [
        "Vainqueur riche",
        "Vainqueur moyen",
        "Vainqueur faible",
        "Non-vainqueur riche",
    ]


def test_leaderboard_returns_at_most_ten_heroes(leaderboard_client) -> None:
    client, engine = leaderboard_client
    with Session(engine) as session:
        session.add_all(
            [make_hero(f"Heros {index}", or_=index) for index in range(12)]
        )
        session.commit()

    response = client.get("/leaderboard")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 10
    assert [entry["or_"] for entry in entries] == list(range(11, 1, -1))


def test_leaderboard_is_accessible_without_authentication(leaderboard_client) -> None:
    client, _engine = leaderboard_client

    response = client.get("/leaderboard")

    assert "Authorization" not in client.headers
    assert response.status_code == 200
