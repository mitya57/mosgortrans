# This file is part of Mosgortrans schedules parser
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>
# License: BSD

from urllib.request import urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from datetime import date

from .backend import Backend, Schedule

base_url = 'http://mosgortrans.org/pass3/request.ajax.php?'
schedule_base_url = 'http://mosgortrans.org/pass3/shedule.php?'

months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

def _parse_date(date_str):
	if len(date_str) <= 1:
		return None
	day, month, year = date_str.split()
	month = months.index(month) + 1
	return date(int(year), month, int(day))

def _find_day(day, days):
	for week in days:
		if week[day] == '1':
			return week
	raise AttributeError('No route for this day found.')

class MgtOrgBackend(Backend):
	'''The mosgortrans.org backend.'''

	def _build_url(self, list, route_type, route=None, day=None, direction=None, waypoint=None):
		d = {'type': route_type.value}
		if list:
			d['list'] = list
		if route:
			d['way'] = route
		if day is not None:
			if isinstance(day, int):
				day = _find_day(day, self.get_days(route_type, route))
			d['date'] = day
		if direction:
			d['direction'] = direction
		if waypoint is not None:
			d['waypoint'] = waypoint
		base = base_url if waypoint is None else schedule_base_url
		url = base + urlencode(d, encoding='cp1251')
		return url

	def _load_list_url(self, list, route_type, route=None, day=None, direction=None):
		url = self._build_url(list, route_type, route, day, direction)
		request = urlopen(url)
		message = request.read().decode('cp1251')
		return message.strip().split('\n')

	def get_routes_by_type(self, route_type):
		return self._load_list_url('ways', route_type)

	def get_days(self, route_type, route):
		return self._load_list_url('days', route_type, route)

	def get_directions(self, route_type, route, day):
		list = self._load_list_url('directions', route_type, route, day)
		if ' -' in list:
			list.remove(' -')
		return list

	def get_waypoints(self, route_type, route, day, direction):
		# Direction must be 'AB' or 'BA'
		return self._load_list_url('waypoints', route_type, route, day, direction)

	def get_schedule(self, route_type, route, day, direction, waypoint):
		schedule = Schedule()
		if waypoint is None:
			waypoint = 'all'
		url = self._build_url(None, route_type, route, day, direction, waypoint)
		request = urlopen(url)
		message = request.read().decode('cp1251')
		soup = BeautifulSoup(message)
		reqform = soup.find('table', 'reqform')
		table1 = reqform.td.table
		table2 = table1.td.table
		tds = table2.find_all('td')
		schedule.created = _parse_date(tds[2].string)
		schedule.valid   = _parse_date(tds[3].string)
		children = list(reqform.children)
		subtitles = children[3:-3:2]
		subtables = children[4:-2:2]
		schedule.schedule = {}
		for subtitle, subtable in zip(subtitles, subtables):
			waypoint = subtitle.h2.string
			schedule.schedule[waypoint] = []
			subtds = subtable.table.find_all('td')
			subtds = zip(subtds[0::2], subtds[1::2])
			for pair in subtds:
				if pair[0].span['class'][0] != 'hour':
					continue
				hour = pair[0].span.string
				schedule.schedule[waypoint] += ['%s:%s' % (hour, span.string)
					for span in pair[1].find_all('span')]
		return schedule
