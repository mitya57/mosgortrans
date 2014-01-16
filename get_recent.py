#!/usr/bin/python3
# Author: 2013 Dmitry Shachnev <d-shachnev@yandex.ru>
# Usage: get_recent.py DAYS (default value 14)

from mgtparser.backend_mgtorg import MgtOrgBackend
from mgtparser.backend_mgtru import MgtRuBackend
from mgtparser.common import RouteType
from datetime import datetime
from sys import argv

backend_org = MgtOrgBackend()
backend_ru = MgtRuBackend()

all_mgtorg_routes = map(backend_org.get_routes_by_type, RouteType)
all_mgtru_routes = map(backend_ru.get_routes_by_type, RouteType)

result = []

period = argv[1] if len(argv) > 1 else 14
now = datetime.now().date()

for route_type, routes in zip(RouteType, all_mgtorg_routes):
	for route in routes:
		for day in backend_org.get_days(route_type, route):
			schedule = backend_org.get_schedule(
				route_type, route, day, 'AB')
			text = ''
			if (now - schedule.created).days < period:
				text = 'NEW!'
				result.append((route_type, route, day, schedule.created))
			print(route_type, route, day, schedule.created, text)

for route_type, routes in zip(RouteType, all_mgtru_routes):
	for route in routes:
		route_info = backend_ru.get_route_info(route_type, route)
		for date_info in route_info:
			day = date_info[0]
			schedule = backend_ru.get_schedule_from_route_info(
				route_info, day, 'AB', 0)
			text = ''
			if (now - schedule.created).days < period:
				text = 'NEW!'
				result.append((route_type, route, day, schedule.created))
			print(route_type, route, day, schedule.created, text)

print('--------------')
print('NEW SCHEDULES:')
print('--------------')

for i in result:
	print(*i)
