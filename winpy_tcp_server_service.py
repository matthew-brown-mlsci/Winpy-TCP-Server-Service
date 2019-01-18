"""

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

me:  Matthew.Brown1@ascension.org

"""

import subprocess
import signal
import tempfile
import win32api
import cgi
import inspect 

import sys
import time
import os
import datetime
import random
import re

import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil
import datetime
import select

from _thread import *
import threading

logging = 1
logfile = "C:\\windows\\temp\\windows_tcp_server_service_log.txt"

#Make logging a little easier
def log_entry(log_message):
	with open(logfile, 'a') as f:
		f.write(str(datetime.datetime.now()) + " : ")
		f.write(log_message + '\n')
		


def client_connected_thread(client_socket, address, netstat_msg):
	#client_socket.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))
	client_socket.settimeout(10)
	try:
		while True:
			client_socket.send(('Options:\n').encode())
			client_socket.send(('* netstat -nbo\n').encode())
			client_socket.send(('* openfiles\n').encode())
			client_socket.send(('* get procs with pids\n').encode())
			client_socket.send(('* exit\n\n').encode())
			client_socket.send(('winpy> ').encode())
			
			# data received from client
			data = client_socket.recv(1024)
			if not data:
				#log_entry('Bye')
				#log_entry("Connection closed from " + str(address))
				# lock released on exit
				#print_lock.release()
				break
			# reverse the given string from client
			if data.decode('ascii').strip() == 'netstat -nbo':
				client_socket.send(('netstat data requested').encode())
				netstat_proc = subprocess.run(["C:\\Windows\\System32\\netstat.exe", '-nbo'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
				netstat_msg = netstat_proc.stdout.decode('ascii')
				client_socket.send(netstat_msg.encode())
			if data.decode('ascii').split(' ')[0] == 'openfiles':
				#openfiles /query /s mlabwifile01
				client_socket.send(('openfiles data requested').encode())
				cmd_args = data.decode('ascii').strip().split(' ')
				openfiles_proc = subprocess.run((["C:\\Windows\\System32\\cmd.exe", '/c'] + cmd_args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
				openfiles_msg = openfiles_proc.stdout.decode('ascii')
				openfiles_msg = openfiles_msg + openfiles_proc.stderr.decode('ascii')
				client_socket.send(openfiles_msg.encode())
				pass
			if data.decode('ascii').strip() == 'get procs with pids':
				pscmd = ['PowerShell', '-Command', '& {Get-WmiObject Win32_Process | Where-Object {$_.GetOwner().User -eq a78808} | Select-Object ProcessID,Name,Owner}']
				ps_proc = subprocess.run(pscmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
				ps_msg = ps_proc.stdout.decode('ascii')
				client_socket.send(ps_msg.encode())
				pass
			if data.decode('ascii').strip() == 'exit':
				client_socket.close()
				return
				
		# connection closed
		client_socket.close()
		log_entry("Connection closed from " + str(address))
	except socket.timeout:
		client_socket.close()
		log_entry("Connection closed from " + str(address))
	except:
		log_entry("Unexpected error:", sys.exc_info()[0])

class WinTCP_Service(win32serviceutil.ServiceFramework):
	_svc_name_ = "WinPy TCP Server Service"
	_svc_display_name_ = "WinPy TCP Server Service"
	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
		socket.setdefaulttimeout(60)
	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)
	def SvcDoRun(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind(('', 9140))
		server_socket.listen(5)
		log_entry("Tcp Server Service Started")
		log_entry("Listening on port 9140")
		rc = None
		read_list = [server_socket]
		
		while rc != win32event.WAIT_OBJECT_0:
			try:
				read_list = [server_socket]
				readable, writable, errored = select.select(read_list, [], [], 1)
			except:
				log_entry("Unexpected error (spot #1):" + str(sys.exc_info()[0]))
				log_entry(str(inspect.currentframe().f_back.f_lineno))
				log_entry(str(inspect.currentframe().f_back.f_locals))
				log_entry(str(inspect.currentframe().f_back.f_code))
				log_entry(str(inspect.currentframe().f_back.f_globals))
				time.sleep(1)
			#log_entry("line spot #2")
			try:
				for s in readable:
					if s is server_socket:
						client_socket, address = server_socket.accept()
						read_list.append(client_socket)
						log_entry("Connection from" + str(address))
						netstat_msg = 'deprecated'
						start_new_thread(client_connected_thread, (client_socket,address,netstat_msg))
			except:
				log_entry("Unexpected error (spot #2):" + str(sys.exc_info()[0]))
				log_entry(str(inspect.currentframe().f_back.f_lineno))
				log_entry(str(inspect.currentframe().f_back.f_locals))
				log_entry(str(inspect.currentframe().f_back.f_code))
				log_entry(str(inspect.currentframe().f_back.f_globals))
			try:
				rc = win32event.WaitForSingleObject(self.hWaitStop, 0)
			except:
				log_entry("Unexpected error (spot #3):" + str(sys.exc_info()[0]))
				log_entry(str(inspect.currentframe().f_back.f_lineno))
				log_entry(str(inspect.currentframe().f_back.f_locals))
				log_entry(str(inspect.currentframe().f_back.f_code))
				log_entry(str(inspect.currentframe().f_back.f_globals))
		
		log_entry("Tcp Server Service STOP requested from Windows Service control, shutting down.")
		
if __name__ == '__main__':
	if logging:
		log_entry("Service started")
		log_entry(os.getlogin())
	if len(sys.argv) == 1:
		servicemanager.Initialize()
		servicemanager.PrepareToHostSingle(WinTCP_Service)
		servicemanager.StartServiceCtrlDispatcher()
	else:
		win32serviceutil.HandleCommandLine(WinTCP_Service)
		
		