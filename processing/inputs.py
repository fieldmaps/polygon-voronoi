import subprocess
from psycopg2 import connect
from psycopg2.sql import SQL, Identifier
from .utils import config, logging

logger = logging.getLogger(__name__)


def main(name, file, layer):
    logger.info(f'Starting {name}')
    subprocess.run([
        'ogr2ogr',
        '-overwrite',
        '--config', 'OGR_GEOJSON_MAX_OBJ_SIZE', '2048MB',
        '-lco', 'FID=fid',
        '-lco', 'GEOMETRY_NAME=geom',
        '-lco', 'LAUNDER=NO',
        '-nlt', 'PROMOTE_TO_MULTI',
        '-nln', f'{name}_attr',
        '-f', 'PostgreSQL', 'PG:dbname=polygon_voronoi',
        file, layer,
    ])
    con = connect(database='polygon_voronoi')
    cur = con.cursor()
    query_1 = """
        DROP TABLE IF EXISTS {table_out};
        CREATE TABLE {table_out} AS
        SELECT
            {id} AS id,
            ST_Transform(ST_Multi(ST_Union(
                ST_CollectionExtract(ST_MakeValid(
                    ST_Force2D(ST_SnapToGrid(geom, 0.000000001))
                ), 3)
            )), 4326)::GEOMETRY(MultiPolygon, 4326) as geom
        FROM {table_in}
        GROUP BY id;
        CREATE INDEX ON {table_out} USING GIST(geom);
    """
    drop_tmp = """
        ALTER TABLE {table_attr}
        DROP COLUMN IF EXISTS geom;
    """
    cur.execute(SQL(query_1).format(
        id=Identifier(config['dissolve']),
        table_in=Identifier(f'{name}_attr'),
        table_out=Identifier(f'{name}_00'),
    ))
    cur.execute(SQL(drop_tmp).format(
        table_attr=Identifier(f'{name}_attr'),
    ))
    con.commit()
    cur.close()
    con.close()
    logger.info(f'Finished {name}')
