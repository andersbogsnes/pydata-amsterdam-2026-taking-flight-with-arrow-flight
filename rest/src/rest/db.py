import sqlalchemy as sa

meta = sa.MetaData()


rides_table = sa.Table(
    "rides",
    meta,
    sa.Column("ride_id", sa.Text, primary_key=True),
    sa.Column("rideable_type", sa.Text, nullable=False),
    sa.Column("started_at", sa.DateTime, nullable=False),
    sa.Column("ended_at", sa.DateTime, nullable=False),
    sa.Column("start_station_name", sa.String, nullable=False),
    sa.Column("start_station_id", sa.String, nullable=False),
    sa.Column("end_station_name", sa.String, nullable=True),
    sa.Column("end_station_id", sa.String, nullable=True),
    sa.Column("start_lat", sa.Float, nullable=True),
    sa.Column("start_lng", sa.Float, nullable=True),
    sa.Column("end_lat", sa.Float, nullable=True),
    sa.Column("end_lng", sa.Float, nullable=True),
    sa.Column("member_casual", sa.String, nullable=False),
    sa.Column("partition_seq", sa.BigInteger, sa.Identity(always=True)),
)
