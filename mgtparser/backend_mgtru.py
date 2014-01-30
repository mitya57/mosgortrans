# This file is part of Mosgortrans schedules parser
# Author: 2014 Dmitry Shachnev <d-shachnev@yandex.ru>
# License: BSD

from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import date

from .backend import Backend, Schedule
from .common import RouteType

base_url = 'http://www.mosgortrans.ru/rasp/'

def _parse_days(days_str):
	if days_str == 'БУДНИ':
		return '1111100'
	if days_str == 'ВЫХОДНЫЕ':
		return '0000011'
	if days_str == 'БУДНИ, ВЫХОДНЫЕ':
		return '1111111'
	weekdays = 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'
	return ''.join([str(int(wd in days_str)) for wd in weekdays])

def _parse_date(date_str):
	if not date_str:
		return None
	return date(*map(int, reversed(date_str.split('.'))))

def _fix_url(rel_link):
	return 'http://mosgortrans.ru/rasp' + rel_link[1:]

def _get_url_pattern(route_type):
	if route_type == RouteType.Auto:
		return '/1/'
	if route_type == RouteType.Trol:
		return '/2/'
	if route_type == RouteType.Tram:
		return '/3/'

class MgtRuBackend(Backend):
	'''The mosgortrans.ru backend.'''

	def __init__(self):
		request = urlopen(base_url)
		message = request.read().decode('utf-8')
		# Fix syntax errors
		message = message.replace('</td></tr><td>', '</td></tr><tr><td>')
		soup = BeautifulSoup(message)
		table = soup.find('table', 'tblroute')
		links = table.find_all('a')
		self.routes = [(link.string, _fix_url(link['href'])) for link in links]

	def _get_route_url(self, route_type, route):
		pattern = _get_url_pattern(route_type)
		for r, url in self.routes:
			if r == route and pattern in url:
				return url

	def get_routes_by_type(self, route_type):
		pattern = _get_url_pattern(route_type)
		return [r for r, url in self.routes if pattern in url]

	def get_route_info(self, route_type, route):
		url = self._get_route_url(route_type, route)
		request = urlopen(url)
		message = request.read().decode('utf-8')
		# Fix syntax error
		message = message.replace('</th><tr>', '</th></tr>')
		soup = BeautifulSoup(message)
		table = soup.table
		trs = table.find_all('tr')[1:]
		result = []
		for tr in trs:
			tds = tr.find_all('td')
			result.append((
				_parse_days(tds[0].string),
				_parse_date(tds[1].string),
				_parse_date(tds[2].string),
				url.replace('index.html', tds[3].a['href'][2:])
			))
		return result

	def get_days(self, route_type, route):
		route_info = self.get_route_info(route_type, route)
		return [date_info[0] for date_info in route_info]

	def get_waypoints_page(self, url):
		request = urlopen(url)
		message = request.read().decode('utf-8')
		soup = BeautifulSoup(message)
		table = soup.find('table', 'tblstop')
		tds = table.find_all('td')
		direction_ths = table.find_all('th')
		waypoints_page = []
		for ind, th in enumerate(direction_ths):
			direction_name = th.string
			dirtds = tds[ind::len(direction_ths)]
			links = [dirtd.a for dirtd in dirtds if dirtd.a]
			waypoints_page.append((direction_name, [(link.string,
				url.replace('index.html', link['href'][2:]))
				for link in links]))
		return waypoints_page

	def get_directions(self, route_type, route, day):
		route_info = self.get_route_info(route_type, route)
		for date_info in route_info:
			if date_info[0] == day or (
			isinstance(day, int) and date_info[0][day] == '1'):
				url = date_info[3]
		waypoints_page = self.get_waypoints_page(url)
		return [name for name, links in waypoints_page]

	def get_waypoints(self, route_type, route, day, direction):
		route_info = self.get_route_info(route_type, route)
		for date_info in route_info:
			if date_info[0] == day or (
			isinstance(day, int) and date_info[0][day] == '1'):
				url = date_info[3]
		waypoints_page = self.get_waypoints_page(url)
		direction = waypoints_page[direction == 'BA'][1]
		return [waypoint for waypoint, url in direction]

	def get_schedule_from_route_info(self, route_info, day, direction, waypoint):
		schedule = Schedule()
		for date_info in route_info:
			if date_info[0] == day or (
			isinstance(day, int) and date_info[0][day] == '1'):
				schedule.created, schedule.valid, url = date_info[1:]
		waypoints_page = self.get_waypoints_page(url)
		direction = waypoints_page[direction == 'BA'][1]
		if waypoint is not None:
			direction = (direction[waypoint],)
		schedule.schedule = {}
		for waypoint_name, url in direction:
			request = urlopen(url)
			message = request.read().decode('utf-8')
			soup = BeautifulSoup(message)
			table = soup.table
			subtds = table.find_all('td')
			subtds = zip(subtds[0::2], subtds[1::2])
			result = []
			for pair in subtds:
				hour = pair[0].string
				minutes = list(pair[1].children)[0::2]
				result += ['%s:%s' % (hour, minute)
					for minute in minutes if minute != '\xa0']
			schedule.schedule[waypoint_name] = result
		return schedule

	def get_schedule(self, route_type, route, day, direction, waypoint):
		route_info = self.get_route_info(route_type, route)
		return self.get_schedule_from_route_info(route_info, day, direction, waypoint)
