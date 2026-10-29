import hashlib
import json

from sqlalchemy import MetaData, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_factory.destinations.base import BaseDestination
from data_factory.transform import to_python_nulls


class PostgresDestination(BaseDestination):
    def __init__(self, engine, schema="olist"):
        self.engine = engine
        self.schema = schema
        self.metadata = MetaData()
        self.metadata.reflect(bind=engine, schema=schema)

    def _table(self, table_name):
        return self.metadata.tables[f"{self.schema}.{table_name}"]

    def write_clean(self, table_name, chunk):
        if chunk.empty:
            return
        statement = pg_insert(self._table(table_name)).on_conflict_do_nothing()
        records = to_python_nulls(chunk).to_dict(orient="records")
        with self.engine.begin() as connection:
            connection.execute(statement, records)

    def write_quarantine(self, table_name, chunk):
        if chunk.empty:
            return
        payloads = json.loads(
            chunk.drop(columns=["reason_code"]).to_json(orient="records", date_format="iso")
        )
        records = [
            {
                "source_table": table_name,
                "reason_code": reason_code,
                "raw_record": payload,
                "record_hash": hashlib.md5(
                    json.dumps(payload, sort_keys=True).encode("utf-8")
                ).hexdigest(),
            }
            for reason_code, payload in zip(chunk["reason_code"], payloads)
        ]
        statement = pg_insert(self._table("quarantine")).on_conflict_do_nothing()
        with self.engine.begin() as connection:
            connection.execute(statement, records)

    def read_keys(self, table_name, column):
        table = self._table(table_name)
        with self.engine.connect() as connection:
            rows = connection.execute(select(table.c[column]))
            return {row[0] for row in rows}

    def count_rows(self, table_name):
        table = self._table(table_name)
        with self.engine.connect() as connection:
            return connection.execute(select(func.count()).select_from(table)).scalar_one()

    def replace_frame(self, frame, table_name, dtype_map):
        table = self._table(table_name)
        with self.engine.begin() as connection:
            connection.execute(table.delete())
            frame.to_sql(
                table_name, connection, schema=self.schema, if_exists="append",
                index=False, dtype=dtype_map, chunksize=5_000, method="multi",
            )