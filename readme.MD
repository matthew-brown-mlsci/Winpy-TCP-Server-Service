
This script creates a simple tcp server, on a windows host,
as a windows service.  

Commands run with the credentials of the service, this was created with the intent of giving non-admin 
user processes the ability to use openfiles + netstat -nbo commands on a citrix server, without
giving them access to anything else!  It facilitates an automated script checking key proprietary 
vendor files in order to prevent file handle contention between citrix user session for said
vendor propietary software.

Built using WinPython-64bit-3.6.2.0Qt5

To install you must compile this to a .exe and install as a windows service:

- as administrator, run winpython command prompt (change these as appropriate for the path)
	- set env variables:
	set PYTHONHOME=C:\Scripts\python\WinPython-64bit-3.6.2.0Qt5\python-3.6.2.amd64\
	set PYTHONPATH=C:\Scripts\python\WinPython-64bit-3.6.2.0Qt5\python-3.6.2.amd64\Lib\

- create python service:
  
  run pyinstaller -F --hidden-import=win32timezone winpy_tcp_server_service.py

- dist\winpy_tcp_server_service.exe install

- check windows services (in administrative under ctrl panel), start/stop service from here.

- after service is running, telnet/netcat/connect to port 9140 on the host running the service,
  follow menu for commands!