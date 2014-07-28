#!/usr/bin/python3
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>

from mgtparser.backend_mgtorg import MgtOrgBackend
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
parser.add_argument('-p', '--print-info', help='print short info about the schedule', action='store_true')
parser.add_argument('-O', '--output-dir', help='directory to store downloaded schedules in', default='schedules')
parser.add_argument('-g', '--debug', help='enable debug output', action='store_true')
args = parser.parse_args()

backend_org = MgtOrgBackend()

all_routes = map(backend_org.get_routes_by_type, RouteType)

if args.debug:
	all_routes = list(all_routes)
	print('All routes: %r' % all_routes)

routes_list = None
if args.input_file:
	routes_list = list(get_routes_list(args.input_file))

result = []
now = datetime.now().date()

advanced_mode = args.download or args.print_info

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
	if not (args.download and check_timestamp(schedule.created)):
		return
	print('saving schedule:', route_type.name, route, day, direction)
	dir = path.join(args.output_dir, route_type.name, route, day)
	makedirs(dir, exist_ok=True)
	schedule.save_to_file(path.join(dir, direction + '.json'))

def print_info(schedule):
	if not (args.print_info and check_timestamp(schedule.created)):
		return
	info_string = schedule.get_info_string()
	print('[INFO]', info_string)
	print(info_string, file=times_file)

@retrying_wrapper
def process_org(route_type, route):
	for day in backend_org.get_days(route_type, route):
		schedule = backend_org.get_schedule(
			route_type, route, day, 'AB', None)
		process_route(route_type, route, day, schedule.created)
		if not advanced_mode:
			continue
		save_schedule(route_type, route, day, 'AB', schedule)
		print_info(schedule)
		if len(backend_org.get_directions(route_type, route, day)) > 1:
			schedule = backend_org.get_schedule(route_type,
				route, day, 'BA', None)
			if check_timestamp(schedule.created):
				save_schedule(route_type, route, day,
					'BA', schedule)
				print_info(schedule)

times_file = open(args.output_file, 'w')
for route_type, routes in zip(RouteType, all_routes):
	for route in routes:
		if (not routes_list) or (route_type, route) in routes_list:
			process_org(route_type, route)
times_file.close()
