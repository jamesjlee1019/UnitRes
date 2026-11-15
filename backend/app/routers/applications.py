from fastapi import APIRouter

from app.db import DbSession
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationPublic

router = APIRouter(tags=["Applications"])


@router.post("/applications", response_model=ApplicationPublic, status_code=201)
def create_application(application: ApplicationCreate, db: DbSession):
    record = Application(
        name=application.name,
        email=application.email.lower(),
        phone=application.phone,
        school=application.school,
        move_in_date=application.move_in_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
