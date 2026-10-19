from collections.abc import Sequence

from sqlmodel import Session, select

from app.models.hero import Hero


def get_leaderboard(session: Session) -> Sequence[Hero]:
    statement = (
        select(Hero)
        .order_by(Hero.victoire.desc(), Hero.or_.desc(), Hero.id)
        .limit(10)
    )
    return session.exec(statement).all()
