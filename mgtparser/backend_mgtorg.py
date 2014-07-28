# This file is part of Mosgortrans schedules parser
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>
# License: BSD

import re
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import date

from .backend import Backend, Schedule

base_url = 'http://mosgortrans.org/pass3/request.ajax.php?'
schedule_base_url = 'http://mosgortrans.org/pass3/shedule.php?'

months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

whitespace_re = re.compile(r'[\t\n]')
created_re = re.compile(r'<h3>c</h3></td><td><h3>([^<]+)</h3></td>')
valid_re = re.compile(r'<h3>по</h3></td><td><h3>([^<]+)</h3></td>')
waypoint_re = re.compile(
  r'<tr><td><h2>([^<]+)</h2></td></tr>'
  r'<tr><td align="center" class="bottomwideborder">'
    r'<table border="0" cellspacing="0" cellpadding="0">'
    r'(.+?)'
    r'</table>'
  r'<br></td></tr>')
hour_re = re.compile(
  r'<td align="right" valign="middle" width="45" class="bottomborder" bgcolor="#[ef]+">'
  r'<span class="hour">([^<]+)</span></td>'
  r'<td align="left" valign="middle" width="25" bgcolor="#[ef]+" class="bottomborder">'
    r'(.+?)'
  r'</td>')
minute_re = re.compile(r'<span class="minutes" >([^<]+)</span>')

def _parse_date(date_str):
	if date_str == '&nbsp;':
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
		result = message.strip().split('\n')
		if '' in result:
			result.remove('')
		if ' -' in result:
			result.remove(' -')
		return result

	def get_routes_by_type(self, route_type):
		return self._load_list_url('ways', route_type)

	def get_days(self, route_type, route):
		return self._load_list_url('days', route_type, route)

	def get_directions(self, route_type, route, day):
		return self._load_list_url('directions', route_type, route, day)

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
		message = whitespace_re.sub('', message)
		schedule.created = _parse_date(created_re.search(message).group(1))
		schedule.valid   = _parse_date(valid_re.search(message).group(1))
		schedule.schedule = {}
		for w_match in waypoint_re.finditer(message):
			waypoint = w_match.group(1)
			times = []
			schedule.schedule[waypoint] = []
			for h_match in hour_re.finditer(w_match.group(2)):
				hour = h_match.group(1)
				for m_match in minute_re.finditer(h_match.group(2)):
					time = '%s:%s' % (hour, m_match.group(1))
					times.append(time)
			schedule.schedule[waypoint] = times
		return schedule
