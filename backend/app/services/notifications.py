from sqlalchemy.orm import Session

from app.models import Notification


def notify(
    db: Session,
    recipient_id: int,
    event_type: str,
    title: str,
    body: str,
    *,
    actor_id: int | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> Notification:
    """Add a notification to the caller's transaction; caller commits atomically."""
    item = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        event_type=event_type,
        title=title[:160],
        body=body[:500],
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(item)
    return item
