import psycopg2
import os

def docstring():
	"""Setup GIS tables.
	
	Connects OSM table with altitude table in selected srid 
	"""
	
help(docstring)

host = input("host = ")
port = input("port = ")
dbname = input("db_name = ")
user = input("user = ")
password = input("password (skip while using .pgpass) = ")
d = input("mesh distance = ")
srid = input("mesh coordinate system = ")


conn = psycopg2.connect(
	host = host, 
	port = port, 
	dbname = dbname, 
	user = user,
	password = password
)

cur = conn.cursor()

cur.execute(
	'''drop table if exists osm_nodes;
	create temporary table osm_nodes as
	select 
		id, 
		st_transform(
			ST_GeomFromText('POINT(' || lon::numeric/10000000 || ' '|| lat::numeric/10000000 || ')',
			4326),			 
		{}) geom 
	from 
		planet_osm_nodes;'''.format(srid)
) 
conn.commit()

cur.execute(
	'''drop table if exists nmt_100;
		create temporary table nmt_100(
		x numeric,
		y numeric,
		h numeric
	);'''
)

conn.commit()

with open('malopolskie.txt', 'r') as f:
	cur.copy_from(f, 'nmt_100', sep=' ')
	
conn.commit()

query = '''drop table if exists nmt_100_geom;
			create temporary table nmt_100_geom as
			select
				ST_GeomFromText('POINT('||x||' '||y||')', {}) as geom,	
				h
			from nmt_100;'''.format(srid)

cur.execute(query)

conn.commit()

cur.execute('''create index on osm_nodes using gist(geom)''')
conn.commit()
cur.execute('''create index on nmt_100_geom using gist(geom)''')
conn.commit()

	
cur.execute('''drop table if exists osm_nmt_altitude;
			create table osm_nmt_altitude as
			select			
				distinct on (n.id) n.id,
				n.geom,
				p.h				
			from 
				osm_nodes n, 
				nmt_100_geom p
			where 
				st_dwithin(n.geom, p.geom, {})
			order by			
				n.id, st_distance(n.geom, p.geom);'''.format(d)
)	
conn.commit()

cur.execute('''drop table if exists osm_line;
				create table osm_line as
				select
					osm_id,
					name,
					tags,
					st_transform(way, {}) as geom
					from planet_osm_line;'''.format(srid)
)	
conn.commit()
			

cur.close()
conn.close()

