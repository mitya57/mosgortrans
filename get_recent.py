#!/usr/bin/python3
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>

from mgtparser.backend_mgtorg import MgtOrgBackend
from mgtparser.backend_mgtru import MgtRuBackend
from mgtparser.common import RouteType, get_routes_list
from argparse import ArgumentParser
from datetime import datetime
from functools import wraps
from os import path, makedirs

parser = ArgumentParser()
parser.add_argument('-o', '--output-file', help='file to store schedule creation times in', default='times.txt')
parser.add_argument('-i', '--input-file', help='file to read routes list from')
parser.add_argument('-d', '--days', type=int, help='number of recent days for which schedules should be checked', default=14)
parser.add_argument('-D', '--download', help='download the schedules as JSON files', action='store_true')
parser.add_argument('-O', '--output-dir', help='directory to store downloaded schedules in', default='schedules')
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
	routes_list = list(get_routes_list(args.input_file))

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

def check_timestamp(created):
	return (now - created).days < args.days

def process_route(route_type, route, day, created):
	if check_timestamp(created):
		print(route_type.name, route, day, created, file=times_file)
		print(route_type.name, route, day, created, 'NEW!')
	else:
		print(route_type.name, route, day, created)

def save_schedule(route_type, route, day, direction, schedule):
	print('saving schedule:', route_type.name, route, day, direction)
	dir = path.join(args.output_dir, route_type.name, route, day)
	makedirs(dir, exist_ok=True)
	schedule.save_to_file(path.join(dir, direction + '.json'))

@retrying_wrapper
def process_org(route_type, route):
	for day in backend_org.get_days(route_type, route):
		schedule = backend_org.get_schedule(
			route_type, route, day, 'AB', None)
		process_route(route_type, route, day, schedule.created)
		if args.download:
			if check_timestamp(schedule.created):
				save_schedule(route_type, route, day, 'AB', schedule)
			if len(backend_org.get_directions(route_type, route, day)) > 1:
				schedule = backend_org.get_schedule(route_type,
					route, day, 'BA', None)
				if check_timestamp(schedule.created):
					save_schedule(route_type, route, day,
					'BA', schedule)

@retrying_wrapper
def process_ru(route_type, route):
	route_info = backend_ru.get_route_info(route_type, route)
	for date_info in route_info:
		if args.download and check_timestamp(date_info[1]):
			directions = len(backend_ru.get_directions(route_type,
				route, date_info[0]))
			for direction in (('AB', 'BA') if directions > 1 else ('AB',)):
				schedule = backend_ru.get_schedule_from_route_info(
					route_info, date_info[0], direction, None)
				save_schedule(route_type, route, date_info[0],
					direction, schedule)
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
