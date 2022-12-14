from importlib.metadata import metadata
from itertools import count
import json
from operator import truediv
from ssl import Options
from datetime import datetime
from model import schema_api_model as schema
from util.Logger import *
from util.ExecSSH import *
from util.MysqlConnector import *
import re
from typing import Optional
from util.func import *

def notUpdated(return_data):
	if return_data=='':
		return True
	return False

### mha에서 하루치 업데이트 된 로그만 가져오기
def batchWork():
	print("start up")

	global lastday
	# 배치 당겨온 기록 남기기
	workday = datetime.datetime.today().strftime("%Y%m%d")

	Log = Logger("./logs/{}.log".format(workday), 0)

	Log.write_log(3, "[LUMOS][Report] Call Received\n")	
	# mha ssh 접속해서 지금까지 업데이트 된 내역 가져오기
	shell = ExecSSH(host='mha-practice.ay1.krane.9rum.cc', user='deploy', logger=Log)
	#1. ls -al 확인하기 - manager, service_name, issue type, logfile, result
	print0="{print $0}"
	print9="{print $9}"
	cmd1=f"ls -al /data/* | grep ^- | awk '{print9}' | awk -F '[._]' '$4 >= {lastday} {print0}'"
 	# cmd1=f"ls -al /data/*/* | grep ^- | awk '{print9}' | awk -F '[._]' '$4 >= {lastday} {print0}'"
	exit_status1, stdout1, stderr1 = shell.exec_command(cmd1, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status1), str(stdout1), str(stderr1)))
	
	if notUpdated(stdout1):
		return stdout1

	#2. 각 파일 내용 확인하기 - started_at
	cnt="{cnt}" 
	file_cnt="{file_cnt}"
	cmd2=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);cat $file_path | head -1 | cut -d ' ' -f 1-5;echo '_';cnt=$((cnt+1));done"
	# cmd2=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep 'Phase 1' $file_path | head -1 | cut -d ' ' -f 1-5;echo '_';cnt=$((cnt+1));done"
	exit_status2, stdout2, stderr2 = shell.exec_command(cmd2, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status2), str(stdout2), str(stderr2)))	 

	#3. ls -al 확인하기 - ended_at
	cmd3="ls -al /data/*/* --time-style full-iso | cut -d ' ' -f 6-7"
	exit_status3, stdout3, stderr3 = shell.exec_command(cmd3, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status3), str(stdout3), str(stderr3)))
	
	#4. 각 파일 내용 확인하기 - idc, zone
	cmd4=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep orig_master_host $file_path | head -1;echo '_';cnt=$((cnt+1));done"
	exit_status4, stdout4, stderr4 = shell.exec_command(cmd4, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status4), str(stdout4), str(stderr4)))
	
	#5. 각 파일 내용 확인하기 - issue_detail
	cmd5=f"file_cnt=$({cmd1} | grep failover | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | grep failover | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep HealthCheck $file_path | head -1;echo '_';cnt=$((cnt+1));done"
	# cmd5=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep HealthCheck $file_path | head -1;echo '_';cnt=$((cnt+1));done"
	exit_status5, stdout5, stderr5 = shell.exec_command(cmd5, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status5), str(stdout5), str(stderr5)))

	#6. 각 파일 내용 확인하기 - result
	# cmd6=f"file_cnt=$({cmd1} | grep -e failover -e switch | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | grep -e failover -e switch | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep -A 2 -e 'Switch Report' -e 'Failover Report' $file_path | tail -1;echo '_';cnt=$((cnt+1));done"
	cmd6=f"file_cnt=$({cmd1} | grep -e failover -e switch | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | grep -e failover -e switch | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep -A 2 -e 'Switch Report' -e 'Failover Report' $file_path | tail -1;echo '_';cnt=$((cnt+1));done"
	exit_status6, stdout6, stderr6 = shell.exec_command(cmd6, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status6), str(stdout6), str(stderr6)))	

### 가져온 데이터 파싱
### columns=[manager, service_name, issue_type, issue_detail, logfile, started_at, ended_at, created_at, zone, idc, result]
	# manager, service_name, issue type, logfile 4개
	parsed_enter=stdout1.split('\n') 
	parsed1=[]
	for i in parsed_enter:
		eli=re.split('[.]', i)
		parsed1.append(eli)

	# started_at	
	tmp=stdout2.split('\n')
	parsed2=[]
	
	for i in tmp:
		if len(i)==1:
			continue
		if i[0]=='_':
			parsed2.append(i.lstrip('_'))
		else:
			parsed2.append(i)

	# ended_at
	tmp=stdout3.split('\n')
	parsed3=[]
	for i in tmp:
		eli1=i.split()
		eli2=eli1[0]+' '+eli1[1].split('.')[0]
		parsed3.append(eli2)

	# idc, zone
	tmp=stdout4.split('\n')
	parsed4=[]
	for i in tmp:
		if len(i)==1:
			continue
		parsed4.append(i)

	hosts=[]
	for i in parsed4:
		tmp=i.split()
		for j in tmp:
			if "--orig_master_host" in j:
				hosts.append(j.split('=')[1].split('.')[0])
				break
	print(hosts)
	# issue_detail
	tmp=stdout5.split('\n')
	parsed5=[]
	for i in tmp:
		if len(i)==1:
			continue
		parsed5.append(i)

	issue_details=[]
	for i in range(len(parsed5)):
		if "SSH" in parsed5[i] and "is reachable" in parsed5[i]:
			issue_details.append("mysql")
		else:
			issue_details.append("OS/Network")
	print(parsed5)

	# result
	tmp_result=stdout6.split('\n')
	parsed6=[]
	for i in tmp_result:
		if len(i)==1:
			continue
		parsed6.append(i)

	results=[]
	for i in range(len(parsed6)):
		if "succeeded" in parsed6[i]:
			results.append("succeed")
		else:
			results.append("failure")

### 파싱 데이터 db에 저장
	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')


	result_cnt=0
	failover_err_cnt=0
	for i in range(len(parsed1)):
		manager, service_name, logfile, issue_type, result, started_at, issue_detail, ended_at, zone, idc=parsed1[i][1], parsed1[i][0], parsed_enter[i], parsed1[i][4], "succeed", parsed2[i], "none", parsed3[i], "none", "none"
#rename -> checked
		if issue_type=="renamed":
			issue_type="checked"

		# if len(parsed1[i])>5:
		# 	result=parsed1[i][5]
		if "_" in parsed1[i][4]:
			issue_type=parsed1[i][4].split('_')[0]

		#추가 파싱 - started_at
		tmp1=started_at.split()
		months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		for j in range(len(months)):
			if months[j] in tmp1[1]:
				tmp1[1]=j+1
				break
		tmp1=list(map(str, tmp1))
		if len(tmp1[1])==1:
			tmp1[1]='0'+tmp1[1]
		started_at=tmp1[4]+"-"+tmp1[1]+"-"+tmp1[2]+" "+tmp1[3]
		
		#추가 파싱 - idc, zone
		if hosts[i]=="sun-partition-my1":
			hosts[i]="db-mha-my1"
		if hosts[i]=="sun-partition-my2":
			hosts[i]="db-mha-my2"

		idc_zone=get_ims_info_by_host_name(hosts[i]).json()
		print(idc_zone)

		zone="server may be destroyed."
		idc="server may be destroyed."
		if "status" not in idc_zone:
			if "message"  not in idc_zone:
				zone=idc_zone['results'][0]['server_type']
				idc=idc_zone['results'][0]['loc_b']
		
		if zone=="":
			zone="none"

		#추가 파싱 - result
		# result_cnt=0
# switch->switching 수정
# 		if issue_type=="switching" or issue_type=="failover": # failover_completes는 따로 있음
# ## 추가			
# 			if issue_type=="failover" and "err" in logfile:
# 				results[result_cnt]="failure"

# 			result=results[result_cnt]
# 			result_cnt+=1

		if issue_type=="failover" and "err" in logfile:
			results[result_cnt]="failure"
			result=results[result_cnt]
			result_cnt+=1
		if issue_type=="switching":
			result=results[result_cnt]
			result_cnt+=1
	
		#추가 파싱 - issue_detail
		if issue_type=="failover":
			issue_detail=issue_details[failover_err_cnt]
			failover_err_cnt+=1

		query =f'insert into metadata(manager, service_name, logfile, issue_type, result, started_at, issue_detail, ended_at, zone, idc) values("{manager}", "{service_name}", "{logfile}", "{issue_type}", "{result}", "{started_at}",  "{issue_detail}", "{ended_at}", "{zone}", "{idc}")'
		ret=dbconn.execdml(query) # 0, 1

	lastday=workday
	return ret



### 초기화 - 맨 처음 가동 시 적용
dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
query =f'select created_at from metadata order by id desc limit 1;'
rows=dbconn.execsql(query)
rows_cnt=len(rows)

lastday=0

if rows_cnt!=0: # 배치작업이 한번이라도 수행되었다면
#	print(int(rows[0][0].strftime("%Y%m%d")))
	lastday=int(rows[0][0].strftime("%Y%m%d"))

batchWork()



