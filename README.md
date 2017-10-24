# pi-minilog
A small data logging tool running on the Raspberry Pi that offers a web interface for real time monitoring of the GPIO states and accessing the log files.

## Setup
Requires the CherryPy web application framework for Python and the RPi.GPIO python package. Both are automatically installed by running the provided setup shell script (setup.sh) with superuser privileges.

## Standard Configuration
* Standard username is "admin", standard password "root", these can be changed by changing the _user_dict_ parameter to a dictionary containing all allowed usernames and corresponding passwords.
* Standard port mappings are for the Raspberry Pi 3 Model B, but other port mappings can be used by setting the _map_port_pin_ parameter to a dictionary containing the desired mapping. The dictionary's keys need to equal the GPIO port numbers, while the values are the Pi's corresponding physical port number.
* Standard log file name is "minilog.log". This can be changed by setting the _logfile_ parameter to the desired file name.
* Standard TCP port for the webserver is 8080, but can be changed in line 293 of main.py.
