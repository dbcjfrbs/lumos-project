# -*- coding: utf-8 -*- 
#원격으로 SSH 명령 실행 및 결과 반환
from util.TermColor import colors
from scp import SCPClient, SCPException
import paramiko 
import time

class ExecSSH:
	def __init__(self, host, user='deploy', logger=None):
		
		self.host = host
		self.user = user
		self.logger = logger
		self.buff_size = 2048		
		self.pause = 0.1

#		key = paramiko.RSAKey.from_private_key_file('/Users/kakao/.ssh/id_rsa')
		key = paramiko.RSAKey.from_private_key_file('/home/deploy/.ssh/id_rsa')
		self.cli = paramiko.SSHClient()
		self.cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		try:


			self.cli.connect(self.host, port=22, username=self.user, pkey=key)



			if self.logger:
				self.logger.write_log(3,"Connect Complete ("+self.user+"@"+str(self.host)+")\n")
			else:
				print('Connect Complete ('+self.user+'@'+str(self.host)+')')
		except Exception as e:
			if self.logger:
				self.logger.write_log(1,"SSH Connect Error: {}".format(e))
			else:
				print(e)
			self.__del__()

	def __del__(self):
		self.cli.close()
		if self.logger:
			self.logger.write_log(3,"Disconnect Complete ("+self.user+"@"+str(self.host)+")\n")
		else:
			print('Disconnect Complete ('+self.user+'@'+str(self.host)+')')

	#명령어를 파일로 실행할 때 사용하는 함수 
	def exec_file(self, filepath, user='deploy', printing='NO'):
		stdout_list = []
		stderr_list = []
		try:
			with open(filepath, 'r') as f:
				cmds = f.readlines()
				for command in cmds:
					cmd = command.rstrip('\n')
					if len(cmd) and '###' not in cmd:
						exit_status, stdout, stderr = self.exec_command(cmd, user, printing)
						stdout_list.append(stdout.rstrip('\n'))
						stderr_list.append(stderr.rstrip('\n'))
						if exit_status:
							break		
				return exit_status, stdout_list, stderr_list

		except Exception as e:
			if self.logger:
				self.logger.write_log(1,"Exec File Error: {}".format(e))
			else:
				print(e)

	def send_file(self, local_path, remote_path):
		try:
			file_name = local_path.split('/')[-1]
			exit_status, stdout, stderr = self.exec_command('stat -c "%U" {}'.format(remote_path))
			if stdout != 'deploy':
				with SCPClient(self.cli.get_transport()) as scp:
					scp.put(local_path, '/home/deploy', preserve_times=True)

				if stdout == 'root':
					exit_status, stdout, stderr = self.exec_command('chown root:root ~deploy/{}'.format(file_name), 'root')

				elif stdout == 'mysql':
					exit_status, stdout, stderr = self.exec_command('chown mysql:mysql ~deploy/{}'.format(file_name), 'root')
					exit_status, stdout, stderr = self.exec_command('mv ~deploy/{} {}'.format(file_name, remote_path), 'root')
			else:
				with SCPClient(self.cli.get_transport()) as scp:
					scp.put(local_path, remote_path, preserve_times=True)

			return True

		except Exception as e:
			if self.logger:
				self.logger.write_log(1,"Send File Error: {}".format(e))
			else:
				print("Send File Error: {}".format(e))
			return False

	def get_file(self, remote_path, local_path):
		try:
			file_name = remote_path.split('/')[-1]
			exit_status, stdout, stderr = self.exec_command('stat -c "%U" {}'.format(remote_path))
			if stdout != 'deploy':
				exit_status, stdout, stderr = self.exec_command('cp {} /home/deploy'.format(remote_path), 'root')
				exit_status, stdout, stderr = self.exec_command('chown deploy:deploy /home/deploy/{}'.format(file_name), 'root')

			with SCPClient(self.cli.get_transport()) as scp:
				scp.get(remote_path, local_path)

			exit_status, stdout, stderr = self.exec_command('rm /home/deploy/{}'.format(file_name), 'root')
			return True
		
		except Exception as e:
			if self.logger:
				self.logger.write_log(1,"Get File Error: {}".format(e))
			else:
				print("Get File Error: {}".format(e))
			return False
	
	#명령어를 단일로 실행할 때 사용하는 함수 
	def exec_command(self, command, user='deploy', printing='NO'):
		stdout = ''
		stderr = ''
		exit_status = 0

		if '###' not in command and len(command) and not command == '\n':
			sshclicmd = self.cli.get_transport().open_session()
			if user == 'root':
				command = "sudo bash -c \"{}\"".format(command)
			
			if self.logger:
				self.logger.write_log(3,"CMD : "+command)
			else:
				print("CMD : "+command, end='')

			sshclicmd.exec_command(command)

			count=0
			while not sshclicmd.exit_status_ready():
				time.sleep(self.pause)
				if sshclicmd.recv_ready(): 
					received = str(sshclicmd.recv(self.buff_size).decode('utf-8')).rstrip('\n')
					stdout += received

					if printing == 'YES':
						if self.logger:
							self.logger.write_log(3,received)
						else:
							print(received, end='')
				else : pass
	
				if sshclicmd.recv_stderr_ready():
					received = str(sshclicmd.recv_stderr(self.buff_size).decode('utf-8')).rstrip('\n')
					stderr += received
					if printing == 'YES' :
						if self.logger:
							self.logger.write_log(3,received, header=False)
						else:
							print(received, end='')
				else : pass

				count+=1
				if count*self.pause > 7200 :
					sshclicmd.close()
					stderr='command timeout(2h)'
					break
			
#			print('check1') # 여러 번
			exit_status = sshclicmd.recv_exit_status()
		

			if printing == 'NO':
				if not exit_status:
					if self.logger:
						self.logger.write_log(3," [SUCCEED]\n".format(command), header=False)
					else:
						print(colors.succeed + ' [SUCCEED]' + colors.reset)
				else:	
					if self.logger:
						self.logger.write_log(3,' [ERROR]'+ colors.reset + '\n    --> ' + str(stderr) + '\n', header=False)

					else:
						print(colors.error + ' [ERROR]' + colors.reset + '\n	--> ' + str(stderr))

		'''
		while sshclicmd.recv_ready():
			stdout += str(sshclicmd.recv(self.buff_size).decode('utf-8')).rstrip('\n')
			if printing == 'YES' : 
				print(stdout, end='')
				if not exit_status:
					print(colors.succeed + '[SUCCEED]' + colors.reset )
					stdout += '[SUCCEED]'
				else:
					print(colors.error + '[ERROR]' + colors.reset)
					stdout += '[ERROR]'

		while sshclicmd.recv_stderr_ready():
			stderr += str(sshclicmd.recv_stderr(self.buff_size).decode('utf-8')).rstrip('\n')
			if printing == 'YES' : 
				print(stderr, end='')
				if exit_status:
					print(colors.error + '[ERROR]' + colors.reset)
					stderr += '[ERROR]'
		'''
		return exit_status, stdout, stderr







