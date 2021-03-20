import re
import sqlite3
from subprocess import run
from configparser import ConfigParser
from pathlib import Path

cwd = Path(__file__).parent
cfg = ConfigParser()
cfg.read((cwd / '../config.ini').resolve())
config = cfg['default']


def get_gpkg_layers(file):
    query = """
        SELECT table_name, geometry_type_name
        FROM gpkg_geometry_columns
        WHERE geometry_type_name IN ('POLYGON', 'MULTIPOLYGON');
    """
    con = sqlite3.connect(file)
    cur = con.cursor()
    layers = sorted([row[0] for row in cur.execute(query)])
    cur.close()
    con.close()
    return layers


def is_polygon(file):
    regex = re.compile(r'\((Multi Polygon|Polygon)\)')
    result = run(['ogrinfo', file], capture_output=True)
    return regex.search(str(result.stdout))


def apply_func(name, file, layer, *args):
    for func in args:
        func(name, file, layer)