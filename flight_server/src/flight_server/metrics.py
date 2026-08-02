import math

import polars as pl

KM_PER_DEGREE = 111.32
DEG_TO_RAD = math.pi / 180.0


def calculate_manhattan(df: pl.DataFrame) -> pl.DataFrame:

    avg_lat_rad = pl.mean_horizontal("start_lat", "end_lat").mul(DEG_TO_RAD)

    return df.select(
        pl.col("ride_id"),
        (
            (pl.col("start_lng") - pl.col("end_lng")).abs()
            * KM_PER_DEGREE
            * avg_lat_rad.cos()
            + (pl.col("start_lat") - pl.col("end_lat")).abs() * KM_PER_DEGREE
        ).alias("manhattan_distance_km"),
    )
