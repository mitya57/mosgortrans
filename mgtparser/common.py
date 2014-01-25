# This file is part of Mosgortrans schedules parser
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>
# License: BSD

from enum import Enum

class RouteType(Enum):
	'''Enumeration describing various route types.

	Possible values: RouteType.Avto, RouteType.Trol, RouteType.Tram.'''
	Auto = 'avto'
	Trol = 'trol'
	Tram = 'tram'

def get_routes_list(filename):
	'''Reads the routes list from the given file.

	:param filename: file name
	:type filename: string
	:rtype: generator of (:class:`RouteType`, string) tuples
	'''
	with open(filename) as input_file:
		for line in input_file:
			if ' ' in line:
				rtype, route = line.split()
				yield (RouteType(rtype), route)
			else:
				yield (RouteType.Auto, line.rstrip())
