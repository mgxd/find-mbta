"""
To make the morning commute easier
Requires google API Key
======
mgxd
"""
import os
from urllib import urlopen
import json
from time import time, strftime, localtime
from datetime import timedelta

import googlemaps

def read_file(fn):
	""" Read and return file content as string """
	with open(fn, 'r') as fp:
		data = fp.read().strip()
	return data

class Stop():
	""" Supports parsing MTBA-API's predictionbystop """
	def __init__(self, stopid, mode="Bus"):
		self.stopid = stopid
		self.mode = mode
		self.url = self.get_url()
		self.data = self.get_data()
		self.alerts = self.get_alerts()
		self.routes = self.get_routes()
		# print stop of interest
		self.show_alerts()

	def show_alerts(self):
		""" Print any warnings on routes """
		for route, alert in self.alerts.items():
			print('WARNING: {0}'.format(alert))

	def get_url(self):
		""" Get info from stopID
		Returns api url """
		format = 'json' # provide others as well in future
		# using public api key atm
		base = ('http://realtime.mbta.com/developer/api/v2/'
				'predictionsbystop?api_key=wX9NwuHnZU2ToO7GmGR9uw')
		return '{0}&stop={1}&format={2}'.format(base, self.stopid, format)

	def get_stop(self):
		""" Print name of stop 
		Returns stop name """
		return self.data['stop_name']

	def get_data(self):
		""" Open MBTA info 
		Returns data dictionary """
		return json.loads(urlopen(self.url).read())

	def get_alerts(self):
		""" Get alerts for each route 
		Returns dictionary pair of route and alert in string """
		alerts = {}
		has_alerts = self.data['alert_headers']
		if has_alerts:
			for alert in has_alerts:
				# route name second word in header text
				route = alert['header_text'].split(' ')[1]
				alerts[route] = alert['header_text']
		return alerts

	def get_routes(self):
		""" Get possible routes from bus stop
		Returns dictionary of routes: route info """
		routes = {}
		modes = self.data['mode']
		for mode in modes:
			# Bus / Train / Hot-Air Balloon
			if mode['mode_name'] == self.mode:
				for route in mode['route']:
					routes[route['route_name']] = route['direction'][0]['trip']
		return routes

	def locate_buses(self):
		""" Parse routes dictionary for bus location and last ping
		Returns list of bus route, tuple of lat/lng, delay since 
		last ping (sec) """
		buses = []
		for key, val in self.routes.items():
			if 'vehicle' in val[0]:
				bus = val[0]['vehicle']
				getinfo = lambda x: float(bus[x])
				delay = int(time() - getinfo('vehicle_timestamp'))
				location = (getinfo('vehicle_lat'), getinfo('vehicle_lon'))
				buses.append([key, location, delay])
			else:
				# no vehicle data for that route
				continue 
		return buses


class GCode():
	""" Supports coordinates or address string - allows for travel calculations """
	def __init__(self, address):
		self.address = address

	def coordinates(self):
		""" Parse address string for lat/lng pair 
		Returns tuple with latitude/longitude """
		data = gmaps.geocode(self.address)[0]['geometry']['location']
		return (data['lat'], data['lng'])

	def get_travel_time(self, dst, mode):
		""" Calculate travel time to string address or coordinates depending on mode
		Returns travel time in seconds """
		data = gmaps.directions(self.address, dst, mode=mode)
		# multiple legs ever?
		secs = data[0]['legs'][0]['duration']['value']
		return secs


def main():
	# create bus stop object
	mbta = Stop('1046', mode='Bus')
	stop = mbta.get_stop()
	print('Information for {0}:'.format(stop))
	# time in secs walking from home to stop
	walk = GCode(stop).get_travel_time(HOME, 'walking')
	# keep track of buses routes, time to leave the house
	arrival_times = {}
	buses = mbta.locate_buses()
	for i, bus in enumerate(buses):
		# seconds from current location to stop minus last ping, 
		# walk to stop, put away laptop and lock doors
		prep = 60 # preparation before leaving
		dist = (GCode(bus[1]).get_travel_time(stop, 'driving')
				- bus[2] - walk - prep)
		if dist <= 0:
			continue
		if bus[0] not in arrival_times:
			arrival_times[bus[0]] = dist
		else:
			# in case there are two of the same bus in the list
			key = bus[0] + '_2'
			arrival_times[key] = dist
	# show routes, time left to leave
	to_local = lambda time: strftime('%H:%M:%S', localtime(time))
	for route, secs in arrival_times.items():
		leaveby = time() + secs
		print('\nRoute {0} :::: Leave by {1}'.format(route, to_local(leaveby)))

if __name__ == '__main__':
	# grab google's API key
	base = '/Users/MathiasMacbook'
	API_KEY = read_file(os.path.join(base, '.googleAPIkey'))
	# unless I moved or got fired
	HOME = read_file(os.path.join(base, '.home-addr'))
	WORK = read_file(os.path.join(base, '.work-addr'))
	gmaps = googlemaps.Client(key=API_KEY)
	main()
