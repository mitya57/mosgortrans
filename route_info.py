#!/usr/bin/python3
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>

from mgtparser.backend_mgtorg import MgtOrgBackend
from mgtparser.common import RouteType
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('routes', metavar='route', help='routes to process', nargs='*')
args = parser.parse_args()

backend_org = MgtOrgBackend()

def main():
	for route in args.routes:
		if ' ' in route:
			rtype, route = route.split()
			route_type = RouteType(rtype)
		else:
			route_type = RouteType.Auto
		process_route(route_type, route)

def format_day(day_str):
	if day_str == '1111111':
		return 'единое'
	if day_str == '1111100':
		return 'будни'
	if day_str == '0000011':
		return 'выходные'
	wkdays = ('пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс')
	result = []
	for d in range(7):
		if day_str[d] == '1':
			result.append(wkdays[d])
	return ','.join(result)

def process_route(route_type, route):
	for day in backend_org.get_days(route_type, route):
		print('=== %s %s %s AB ===' % (route_type.name, route, format_day(day)))
		schedule = backend_org.get_schedule(
			route_type, route, day, 'AB', None)
		process_schedule(schedule)
		if len(backend_org.get_directions(route_type, route, day)) > 1:
			print('=== %s %s %s BA ===' % (route_type, route, format_day(day)))
			schedule = backend_org.get_schedule(
				route_type, route, day, 'BA', None)
			process_schedule(schedule)

def is_finish(wp_name):
	return ('к/ст' in wp_name) or ('(выс.)' in wp_name)

def process_schedule(schedule):
	print('Created on %s, valid until %s' % (schedule.created, schedule.valid))
	clr_start = {}
	clr_end = {}
	clr_first = {}
	clr_last = {}
	for waypoint in sorted(schedule.schedule):
		times = schedule.schedule[waypoint]
		for color in 'black', 'green', 'red', 'darkblue', 'pink':
			if color == 'black':
				colored = [t for t in times if t[-1].isdigit()]
			else:
				colored = [t[:-1] for t in times if t.endswith(color[0])]
			if colored:
				if color not in clr_start or is_finish(clr_start[color]):
					clr_start[color] = waypoint
					clr_first[color] = colored[0]
					clr_last[color] = colored[-1]
				clr_end[color] = waypoint
	for color, start in sorted(clr_start.items()):
		print('%s: "%s" to "%s", first %s, last %s' % (
			color, start, clr_end[color], clr_first[color], clr_last[color]
		))

if __name__ == '__main__':
	main()
