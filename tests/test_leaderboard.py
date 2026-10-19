from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.hero import Hero
from app.routes.leaderboard import router


def test_leaderboard_orders_victories_then_gold_and_limits_results(
    tmp_path,
) -> None:
    engine = create_engine(
        URL.create("sqlite", database=str(tmp_path / "leaderboard.db")),
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    heroes = [
        Hero(
            nom=f"Hero{i}",
            classe="guerrier",
            force=6,
            agilite=2,
            intelligence=2,
            pv=32,
            pv_max=32,
            salle_actuelle="entree",
            or_=100 - i,
            victoire=i in (10, 11),
        )
        for i in range(12)
    ]
    with Session(engine) as session:
        session.add_all(heroes)
        session.commit()

    def get_test_session():
        with Session(engine) as session:
            yield session

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_session] = get_test_session

    try:
        with TestClient(test_app) as client:
            response = client.get("/leaderboard")
    finally:
        engine.dispose()

    assert "/leaderboard" in app.openapi()["paths"]
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 10
    assert [hero["victoire"] for hero in results] == [True, True] + [False] * 8
    assert results[0]["or_"] == 90
    assert results[1]["or_"] == 89
