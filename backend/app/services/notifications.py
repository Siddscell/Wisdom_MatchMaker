from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models import Match, Notification, Offering, Requirement
from app.services import email


def notify(db: Session, match_id: str, r: Requirement, o: Offering, score: float) -> bool:
    """Notify both sides once. The status flip new -> notified is the guard, so a match
    can never be notified twice, even with concurrent matching runs."""
    claimed = db.execute(
        update(Match)
        .where(Match.id == match_id, Match.status == "new")
        .values(status="notified", updated_at=func.now())
        .returning(Match.id)
    ).first()
    if claimed is None:
        return False
    messages = [
        (
            "client",
            r.contact_email,
            f'A supplier match was found for "{r.product_requirement}": '
            f"{o.supplier_name} (score {score:g}/100).",
        ),
        (
            "supplier",
            o.contact_email,
            f'A client requirement matches your offer "{o.product_offered}": '
            f"{r.client_name} (score {score:g}/100).",
        ),
    ]
    for role, to, text in messages:
        db.add(
            Notification(match_id=match_id, recipient_role=role, recipient_email=to, message=text)
        )
        email.send(db, to, "New match on Supplier Matchmaker", text)
    return True
