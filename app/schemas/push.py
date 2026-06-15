"""Web Push subscription schemas."""

from pydantic import BaseModel


class PushKeys(BaseModel):
    """Keys from the browser PushSubscription."""

    p256dh: str
    auth: str


class PushSubscribe(BaseModel):
    """A browser Web Push subscription payload."""

    endpoint: str
    keys: PushKeys


class VapidKey(BaseModel):
    """The public VAPID key the client uses to subscribe."""

    public_key: str | None
