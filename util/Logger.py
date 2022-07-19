import ntpath
import os
import datetime
import copy
import sys
import re

NC='\033[0m'
RED='\033[31m'
GREEN='\033[32m'
BLUE='\033[34m'
LIGHT_GRAY='\033[37m'
CYAN='\033[36m'
BLINK_RED='\033[5;31m'
BLINK_CYAN='\033[5;36m'
BLINK_BLUE='\033[5;34m'
BOLD_BLACK='\033[1;30m'

# log level definition
CRITICAL = 0
ERROR = 1
WARNING = 2
INFO = 3
DEBUG = 4

# log rotate frequency
DAILY = 0
WEEKLY = 1
MONTHLY = 2
YEARLY = 3

# rotate flag
ROTATE_OFF = 0
ROTATE_FILE = 1
ROTATE_DAILY = 2

#filesize preset
KB = 1024
MB = 1048576
GB = 1073741824

loglevel_threshold = 4

class Logger:
	def trans_filesize(self, filesize):
		unit = filesize[-1].upper()
		num = int(filesize[:len(filesize)-1])
		return {'B':num, 'K':KB*num,'M':MB*num,'G':GB*num}[unit]

	def __init__(self, filename, mode, log_size="0B", log_count=0):
		self.filename = filename
		self.mode = mode
		self.log_size = self.trans_filesize(log_size)
		self.log_count = log_count
		self.start_day = datetime.date.today()
		self.directory = os.path.split(filename)[0]
		self.basename = os.path.split(filename)[1]
		self.fileext = os.path.splitext(self.basename)[1]
		self.basename = os.path.splitext(self.basename)[0]
		self.rotate_number=0
		self.openfile_size=0
		self.f=None

		if self.directory == "":
			self.directory = os.getcwd()

		self.directory = self.directory+'/'

		#print(self.directory+' '+self.basename+' '+self.fileext);
		try:
			if mode == ROTATE_OFF:
				open_filename = self.basename+self.fileext
			elif mode == ROTATE_FILE:
				p = re.compile(self.basename+self.fileext+'\d+')
				file_list = [file for file in os.listdir(self.directory) if p.match(self.basename+self.fileext)]
				if len(file_list) == 0:
					open_filename = self.basename+self.fileext+'0'
				else:
					open_filename = max(file_list, key=lambda x: os.stat(os.path.join(self.directory, x)).st_mtime)
				self.rotate_number = int(open_filename[len(self.basename)+len(self.fileext):])
			elif mode == ROTATE_DAILY:
				open_filename = self.basename+str(self.start_day)+self.fileext
			else:
				raise Exception('rotate mode list : {0: OFF, 1: ROTATE_FILE, 2: ROTATE_DAILY}')
			self.f=open(self.directory+open_filename,'at')
			self.openfile_size = os.path.getsize(self.directory+open_filename)
		except OSError as e:
			print('cannot open', filename,' :', e)
		except Exception as e:
			print("Unexpected error:", e)
		

	def __del__(self):
		if self.f is not None:
			self.f.close()

	def get_header(self,loglevel):
		return {CRITICAL:'CRITICAL', ERROR:'ERROR', WARNING:'WARNING', INFO:'INFO', DEBUG:'DEBUG'}[loglevel];

	def log_rotate(self,context_len):
		# toward_day logic modify
		if self.mode == ROTATE_FILE:
			if self.openfile_size + context_len > self.log_size:
				self.rotate_number = (self.rotate_number+1)%self.log_count
				try:
					self.f.close()
					self.f=open(self.directory+self.basename+self.fileext+str(self.rotate_number),'wt')
					self.openfile_size = 0
				except OSError:
					print('file close/open error ', self.directory+self.basename+self.fileext+str(self.rotate_number))
				except Exception as e:
					print("Unexpected error:", e)
		elif self.mode == ROTATE_DAILY:
			if self.start_day < datetime.date.today():
				self.start_day = datetime.date.today()
				try:
					self.f.close()
					self.f=open(self.directory+self.basename+str(self.start_day)+self.fileext,'wt')
				except OSError:
					print('file close/open error', self.directory+self.basename+str(self.start_day)+self.fileext)
				except Exception as e:
					print("Unexpected error:",e)

	def write_log(self, loglevel, message, header=True):
		if(header):
			context = str(datetime.datetime.today()) + " [" +  self.get_header(loglevel) + "] " + str(message)
		else:
			context = str(message)
		self.log_rotate(len(context))
		if loglevel_threshold >= loglevel:
			try:
				if 'password' in context :
					context = context.replace('password','xxxx')
				self.f.write(context);
				self.f.flush()
			except OSError:
				print('file write error')
			except Exception as e:
				print("Unexpected error:",e)
			self.openfile_size += len(context)
