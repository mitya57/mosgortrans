#!/usr/bin/python3
# Author: 2013 Dmitry Shachnev <d-shachnev@yandex.ru>

from mgtparser.backend_mgtorg import MgtOrgBackend
from mgtparser.backend_mgtru import MgtRuBackend
from mgtparser.common import RouteType
from argparse import ArgumentParser
from datetime import datetime
from functools import wraps

parser = ArgumentParser()
parser.add_argument('-o', '--output-file', help='file to store schedule creation times in', default='times.txt')
parser.add_argument('-i', '--input-file', help='file to read routes list from')
parser.add_argument('-d', '--days', type=int, help='number of recent days for which schedules should be checked', default=14)
parser.add_argument('--ru', help='only search mosgortrans.ru site', action='store_true')
parser.add_argument('--org', help='only search mosgortrans.org site', action='store_true')
args = parser.parse_args()

backend_org = MgtOrgBackend()
backend_ru = MgtRuBackend()

all_mgtorg_routes = map(backend_org.get_routes_by_type, RouteType)
all_mgtru_routes = map(backend_ru.get_routes_by_type, RouteType)

if args.ru:
	all_mgtorg_routes = []
if args.org:
	all_mgtru_routes = []

routes_list = None
if args.input_file:
	routes_list = []
	input_file = open(args.input_file)
	for line in input_file:
		if ' ' in line:
			rtype, route = line.split()
			routes_list.append((RouteType(rtype), route))
		else:
			routes_list.append((RouteType.Auto, line.rstrip()))
	input_file.close()

result = []
now = datetime.now().date()

def retrying_wrapper(function):
	@wraps(function)
	def function_new(*args, **kwargs):
		try:
			function(*args, **kwargs)
		except Exception as e:
			print('Exception: %s; retrying' % e)
			function(*args, **kwargs)
	return function_new

def process_route(route_type, route, day, created):
	if (now - created).days < args.days:
		print(route_type.name, route, day, created, file=times_file)
		print(route_type.name, route, day, created, 'NEW!')
	else:
		print(route_type.name, route, day, created)

@retrying_wrapper
def process_org(route_type, route):
	for day in backend_org.get_days(route_type, route):
		schedule = backend_org.get_schedule(
			route_type, route, day, 'AB')
		process_route(route_type, route, day, schedule.created)

@retrying_wrapper
def process_ru(route_type, route):
	route_info = backend_ru.get_route_info(route_type, route)
	for date_info in route_info:
		process_route(route_type, route, date_info[0], date_info[1])

times_file = open(args.output_file, 'w')
for route_type, routes in zip(RouteType, all_mgtorg_routes):
	for route in routes:
		if (not routes_list) or (route_type, route) in routes_list:
			process_org(route_type, route)
for route_type, routes in zip(RouteType, all_mgtru_routes):
	for route in routes:
		if (not routes_list) or (route_type, route) in routes_list:
			process_ru(route_type, route)
times_file.close()
