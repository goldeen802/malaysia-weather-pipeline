"""PySpark job: per-location forecast statistics over accumulated snapshots.

Runs on the GitHub Actions Linux runner (Java + Spark available there). Pulls the
raw snapshots from BigQuery, aggregates them with the Spark DataFrame API, and
writes the result back to BigQuery.

Data is bridged through pandas to avoid managing the spark-bigquery connector JAR;
in a production cluster you would read Parquet/BigQuery natively with the connector.
"""

import os

from google.cloud import bigquery
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

PROJECT = os.environ["GCP_PROJECT"]
SOURCE_TABLE = f"{PROJECT}.weather_raw.forecast"
TARGET_TABLE = f"{PROJECT}.weather_staging.spark_location_stats"


def read_source(client: bigquery.Client):
    query = f"""
        SELECT location_id, location_name, min_temp, max_temp
        FROM `{SOURCE_TABLE}`
    """
    return client.query(query).to_dataframe()


def aggregate(spark: SparkSession, source_pdf):
    df = spark.createDataFrame(source_pdf)
    df = df.withColumn("temp_range", F.col("max_temp") - F.col("min_temp"))

    stats = df.groupBy("location_id", "location_name").agg(
        F.count("*").alias("forecast_rows"),
        F.round(F.avg("max_temp"), 2).alias("avg_max_temp"),
        F.round(F.stddev("max_temp"), 2).alias("stddev_max_temp"),
        F.round(F.avg("min_temp"), 2).alias("avg_min_temp"),
        F.round(F.avg("temp_range"), 2).alias("avg_temp_range"),
    )

    # Window function: rank locations hottest-first by average max temperature.
    hotness = Window.orderBy(F.col("avg_max_temp").desc())
    return stats.withColumn("hotness_rank", F.row_number().over(hotness))


def write_results(client: bigquery.Client, result_pdf) -> int:
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_dataframe(result_pdf, TARGET_TABLE, job_config=job_config)
    job.result()
    return job.output_rows


def main() -> None:
    client = bigquery.Client(project=PROJECT)
    source_pdf = read_source(client)

    spark = SparkSession.builder.appName("forecast-stats").getOrCreate()
    try:
        result_pdf = aggregate(spark, source_pdf).toPandas()
    finally:
        spark.stop()

    written = write_results(client, result_pdf)
    print(f"Wrote {written} location rows to {TARGET_TABLE}")


if __name__ == "__main__":
    main()
