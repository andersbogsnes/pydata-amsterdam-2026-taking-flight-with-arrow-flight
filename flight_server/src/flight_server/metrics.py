import polars as pl
import pyarrow as pa


def calculate_ctr(df: pa.Table) -> pa.Table:
    df = pl.DataFrame(df)
    ctr = (
        pl.col("is_clicked")
        .sum()
        .truediv(pl.col("is_clicked").len())
        .alias("click_rate")
    )
    return df.select(ctr).to_arrow()
