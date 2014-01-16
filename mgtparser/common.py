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
