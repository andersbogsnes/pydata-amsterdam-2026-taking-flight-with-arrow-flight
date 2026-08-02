import datetime

from pydantic import BaseModel, ConfigDict


class Ride(BaseModel):
    ride_id: str
    rideable_type: str
    started_at: datetime.datetime
    ended_at: datetime.datetime
    start_station_name: str
    start_station_id: str
    end_station_name: str | None = None
    end_station_id: str | None = None
    start_lat: float | None = None
    start_lng: float | None = None
    end_lat: float | None = None
    end_lng: float | None = None
    member_casual: str

    model_config = ConfigDict(from_attributes=True)
