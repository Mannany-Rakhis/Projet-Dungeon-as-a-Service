from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models.hero import Hero
from app.schemas.leaderboard import LeaderboardRead
from app.services.leaderboard_service import get_leaderboard

router = APIRouter(tags=["Classement"])


@router.get("/leaderboard", response_model=list[LeaderboardRead])
def read_leaderboard(
    session: Session = Depends(get_session),
) -> list[Hero]:
    return list(get_leaderboard(session))
