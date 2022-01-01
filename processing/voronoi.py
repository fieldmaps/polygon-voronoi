from psycopg2.sql import SQL, Identifier
from .utils import logging

logger = logging.getLogger(__name__)

query_1 = """
    DROP TABLE IF EXISTS {table_out};
    CREATE TABLE {table_out} AS
    SELECT
        (ST_Dump(
            ST_CollectionExtract(ST_MakeValid(
                ST_VoronoiPolygons(ST_Collect(geom))
            ), 3)
        )).geom::GEOMETRY(Polygon, 4326) AS geom
    FROM {table_in};
    CREATE INDEX ON {table_out} USING GIST(geom);
"""
query_2 = """
    DROP TABLE IF EXISTS {table_out};
    CREATE TABLE {table_out} AS
    SELECT
        a.fid,
        b.geom
    FROM {table_in1} AS a
    JOIN {table_in2} AS b
    ON ST_Within(a.geom, b.geom);
    CREATE INDEX ON {table_out} USING GIST(geom);
"""
query_3 = """
    SELECT *
    FROM {table_in} a
    JOIN {table_in} b
    ON ST_Overlaps(a.geom, b.geom)
    WHERE a.fid != b.fid
    LIMIT 1;
"""
query_4 = """
    DROP TABLE IF EXISTS {table_out};
    CREATE TABLE {table_out} AS
    SELECT
        fid,
        ST_MakePolygon(ST_ExteriorRing(
            (ST_Dump(ST_Union(geom))).geom
        ))::GEOMETRY(Polygon, 4326) AS geom
    FROM {table_in}
    GROUP BY fid;
    CREATE INDEX ON {table_out} USING GIST(geom);
"""
drop_tmp = """
    DROP TABLE IF EXISTS {table_tmp1};
    DROP TABLE IF EXISTS {table_tmp2};
"""


def main(cur, name, *_):
    cur.execute(SQL(query_1).format(
        table_in=Identifier(f'{name}_03'),
        table_out=Identifier(f'{name}_04_tmp1'),
    ))
    cur.execute(SQL(query_2).format(
        table_in1=Identifier(f'{name}_03'),
        table_in2=Identifier(f'{name}_04_tmp1'),
        table_out=Identifier(f'{name}_04_tmp2'),
    ))
    cur.execute(SQL(query_3).format(
        table_in=Identifier(f'{name}_04_tmp2'),
    ))
    if len(cur.fetchall()) > 0:
        raise RuntimeError(
            'Overlaping voronoi polygons, try adjusting segment and/or snap values.')
    cur.execute(SQL(query_4).format(
        table_in=Identifier(f'{name}_04_tmp2'),
        table_out=Identifier(f'{name}_04'),
    ))
    cur.execute(SQL(drop_tmp).format(
        table_tmp1=Identifier(f'{name}_04_tmp1'),
        table_tmp2=Identifier(f'{name}_04_tmp2'),
    ))
    logger.info(name)
