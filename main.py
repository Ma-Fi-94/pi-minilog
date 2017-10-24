# Copyright 2017 Ma-Fi-94
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module contains a webservice implementation that shows
the status of the GPIO pins on a Raspberry Pi 3 Model B
"""

import datetime
import os
import logging
import socket
import cherrypy
import RPi.GPIO as GPIO


class Control(object):
	"""GPIO status view control object"""

	def __init__(self, map_port_pin=None, user_dict=None, logfile=None):
		# Dictionary containing the mapping GPIO port number -> physical pin number.
		# This may have to be changed depending on the type of Raspberry Pi system
		# you are using. Standard values here are for the Raspberry Pi 3 Model B
		default_map = {}
		default_map.update({2: 3, 3: 5, 4: 7, 5: 29, 6: 31, 7: 26, 8: 24, 9: 21})
		default_map.update({10: 19, 11: 23, 12: 32, 13: 33, 14: 8, 15: 10, 16: 36})
		default_map.update({17: 11, 18: 12, 19: 35, 20: 38, 21: 40, 22: 15, 23: 16})
		default_map.update({24: 18, 25: 22, 26: 37, 27: 13})
		self._map_port_pin = map_port_pin or default_map

		# Dictionary of all allowed users and their respective password
		self._user_dict = user_dict or {'admin': 'root'}

		# Set the path and name of the logfile here
		self._logfile = logfile or 'minilog.log'
		self._logstate = False

		# Init pins
		for pin in self._map_port_pin.values():
			self._init_pin(pin)

	@cherrypy.expose
	def index(self):
		"""Start page of the web interface -- returns the login form."""
		return self._get_authform_string()

	@cherrypy.expose
	def log_clear(self):
		"""Empty the log file"""
		open(self._logfile, 'w').close()
		return self._get_overview_table()

	@cherrypy.expose
	def log_get(self):
		"""Show the log file"""
		with open(self._logfile) as logfile:
			logged_content = logfile.read()
			return logged_content.replace('\n', '</br>\n')

	@cherrypy.expose
	def log_now(self):
		"""Log current GPIO state"""
		self._log_pin_event(force=True)
		return self._get_overview_table()

	@cherrypy.expose
	def log_toggle(self):
		"""Toggle the logging state of the device."""
		self._logstate = not self._logstate
		return self.view()

	@cherrypy.expose
	def shutdownserver(self):
		"""Routine for shutting down the server"""
		self._logstate = False
		cherrypy.engine.exit()

	@cherrypy.expose
	def validate(self, uname, pwd):
		"""Routine for verification of entered username / password pair."""
		if uname in self._user_dict.keys() and pwd == self._user_dict[uname]:
			return self.view()
		return self.index()

	@cherrypy.expose
	def view(self):
		"""After successful loging, this routine is called.
		The main overview table showing the current GPIO states is returned.
		"""
		return self._get_overview_table()

	def _get_overview_table(self):
		"""
		Generate the HTML code of the main table showing
		the current sensor state
		"""
		ret = """
		<html>
		<head>
			<meta name="viewport" content="width=device-width, initial-scale=1">
			<style>""" + self._get_css_string() + "</style>" + """
		</head>

		<body>
			<h1> Pi-Minilog </h1>"""

		ret += _html('h2', 'Host Name: %s' % socket.gethostname())
		ret += _html('h2', 'System Time: %s' % datetime.datetime.now())
		logsize = os.path.getsize(self._logfile)
		ret += _html('h2', 'Log File Size: %d Bytes' % logsize)
		ret += _html('h2', 'Current Logging Status: %s' % self._logstate)
		ret += _html('h2', 'Current Sensor States:')
		ret = ret + """
			<table>
				<tr>
					<th>GPIO-Port</th>
					<th>Pin Nb.</th>
					<th>State</th>
				</tr> """

		for port in sorted(self._map_port_pin.keys()):
			gpio_pin = self._map_port_pin[port]
			gpio_state = self._get_pin_input_bool(self._map_port_pin[port])
			row = _html('td', port) + _html('td', gpio_pin) + _html('td', gpio_state)
			ret += _html('tr', row)

		ret += """
			</table>

		<hr><p><p><p>

		<form method="get" action="log_toggle">
			<button style="background-color: #008CBA; float: left;" type="submit">Logging ON/OFF</button>
		</form>

		<form method="get" action="log_now">
			<button style="background-color: #008CBA; float: left;" type="submit">Log Current State</button>
		</form>

		<form method="get" action="log_get">
			<button style="background-color: #008CBA; float: left;" type="submit">Get Log</button>
		</form>

		<form method="get" action="log_clear">
			<button style="background-color: #f44336; float: clear;" type="submit">Delete Log</button>
		</form>

		<p>

		<form method="get" action="view">
			<button style="background-color: #4CAF50; float: left;" type="submit">Reload</button>
		</form>

		<form method="get" action="shutdownserver">
			<button style="background-color: #f44336;  float: clear;" type="submit">Shutdown</button>
		</form>

		</body>
		</html>
		"""

		return ret

	@staticmethod
	def _get_authform_string():
		"""Generate the HTML code of the login form"""

		return """
		<html>
		<head>
			<meta name="viewport" content="width=device-width, initial-scale=1">

			<style>

				body {
					color: #414141;			/* Dark gray */
					background-color: #EEEEEE;	/* Lighter gray*/
				}

			</style>

		</head>
		<body>
			<h1> Pi-Minilog </h1>
			<p>
			<form method="get" action="validate">
				<input type="text" value="" placeholder="Enter Username" name="uname" />
				<br>
				<input type="password" value="" placeholder="Enter Password" name="pwd" />
				<br>
				<button type="submit">Login</button>
				<br>
				<button type="reset">Reset</button>
				<br>
			</form>
		<body></html>
		"""

	@staticmethod
	def _get_css_string():
		"""Generate the CSS code for the HTML pages"""

		return """

		body {
			color: #414141;			/* Dark gray */
			background-color: #EEEEEE;	/* Lighter gray*/
		}

		table {
			width: 40%;
		}

		th {
			height: 50px;
			text-align: left;
		}

		th, td {
			border-bottom: 1px solid #ddd;
		}

		h1 {
			font-size: 34px;
		}

		h2 {
			font-size: 22px;
		}

		h3 {
			font-size: 18px;
		}

		h1, h2, h3, h4, h5, h6 {
			font-family: "Helvetica", "Arial", sans-serif;
			font-weight: normal;
		}

		button {
			width: 180px;
			color: white;
			font-size:18px;
			border-radius: 8px;
		}

"""

	@staticmethod
	def _get_pin_input_bool(pin_nb):
		"""Returns the level of a GPIO port as boolean."""
		return GPIO.input(pin_nb) == GPIO.HIGH

	def _init_pin(self, pin_nb):
		"""
		Routine for setting up a GPIO port as inport port
		and hooking the logging routine to it.
		"""
		logging.debug('Setting up Pin #%d', pin_nb)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(pin_nb, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.add_event_detect(pin_nb, GPIO.BOTH)
		GPIO.add_event_callback(pin_nb, self._log_pin_event)
		return True

	def _log_pin_event(self, force=False):
		"""Write all GPIO state to the log file, whenever an event is triggered"""
		if self._logstate or force:
			logging.debug('LOGGING an event!')
			with open(self._logfile, 'a') as logfile:
				logfile.write(str(datetime.datetime.now()))
				for port in sorted(self._map_port_pin.keys()):
					logfile.write(', %s' % self._get_pin_input_bool(self._map_port_pin[port]))
				logfile.write('\r\n')
		return True


def _html(tag_name, value):
	return '<%s>%s</%s>' % (tag_name, value, tag_name)


# Start the server
logging.basicConfig()
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.config.update({'server.socket_port': 8080})
cherrypy.quickstart(Control())
