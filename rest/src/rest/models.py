import datetime

from pydantic import BaseModel, ConfigDict, TypeAdapter


class Message(BaseModel):
    id: int
    message_id: str
    campaign_id: int
    message_type: str
    client_id: int
    channel: str
    category: str | None
    platform: str | None
    email_provider: str
    stream: str
    date: datetime.date
    sent_at: datetime.datetime
    is_opened: bool
    opened_first_time_at: datetime.datetime | None
    opened_last_time_at: datetime.datetime | None
    is_clicked: bool
    clicked_first_time_at: datetime.datetime | None
    clicked_last_time_at: datetime.datetime | None
    is_unsubscribed: bool
    unsubscribed_at: datetime.datetime | None
    is_hard_bounced: bool
    hard_bounced_at: datetime.datetime | None
    is_soft_bounced: bool
    soft_bounced_at: datetime.datetime | None
    is_complained: bool
    complained_at: datetime.datetime | None
    is_blocked: bool
    blocked_at: datetime.datetime | None
    is_purchased: bool
    purchased_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


Messages = TypeAdapter(list[Message])
