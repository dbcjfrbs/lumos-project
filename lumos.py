from importlib.metadata import metadata
from itertools import count
import json
from ssl import Options
import uvicorn
import fastapi
from datetime import datetime
from model import schema_api_model as schema
from util.Logger import *
from util.ExecSSH import *
from util.MysqlConnector import *
from fastapi_utils.tasks import repeat_every
import re
from typing import Optional
from util.func import *

app = fastapi.FastAPI()



# ### 초기화 - 맨 처음 가동할 때마만 초기화 이후 서버 리로딩할 시에는 적용 안됨
# dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
# query =f'select count(*) from metadata'
# rows=dbconn.execsql(query)[0][0]
# if rows==0: # 배치작업이 한번도 수행되지 않았다면 수행
# 	lastday=0
# else: # 배치작업이 수행된 이후 서버 리로드 시 전날 date로 셋팅
# 	lastday=int(datetime.datetime.today().strftime("%Y%m%d"))-1

# ### mha에서 주기적으로 업데이트 된 로그만 가져오는 스케줄러 : 개발완료 되면 crontab 사용하고 아래 스케줄러는 삭제할 예정
# @app.on_event("startup")
# @repeat_every(seconds=2)
# def batchWork():
# 	print("start up")

# 	global lastday
# 	# 배치 당겨온 기록 남기기
# 	workday = datetime.datetime.today().strftime("%Y%m%d")
# 	Log = Logger("./logs/{}.log".format(workday), 0)
# 	Log.write_log(3, "[LUMOS][Report] Call Received\n")
# 	# mha ssh 접속해서 어제 자정부터 지금까지 업데이트 된 내역 가져오기 
# 	shell = ExecSSH(host='mha-test.ay1.krane.9rum.cc', user='deploy', logger=Log)

# 	#1. ls -al 확인하기 - manager, service_name, issue type, logfile, result
# 	print0="{print $0}"
# 	print9="{print $9}"
# 	cmd1=f"ls -al /data/* | grep ^- | awk '{print9}' | awk -F '[._]' '$4 >= {lastday} {print0}'"
# 	exit_status1, stdout1, stderr1 = shell.exec_command(cmd1, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status1), str(stdout1), str(stderr1)))

# 	#2. 각 파일 내용 확인하기 - started_at
# 	cnt="{cnt}" 
# 	file_cnt="{file_cnt}"
# #	cmd2="file_cnt=$(ls -al /data/* | grep ^- | awk '{print $9}' | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$(ls -al /data/* | grep ^- | awk '{print $9}' | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);cat $file_path | head -1 | cut -d ' ' -f 1-5;echo '_';cnt=$((cnt+1));done"
# 	cmd2=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);cat $file_path | head -1 | cut -d ' ' -f 1-5;echo '_';cnt=$((cnt+1));done"
# 	exit_status2, stdout2, stderr2 = shell.exec_command(cmd2, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status2), str(stdout2), str(stderr2)))	                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        

# 	#3. ls -al 확인하기 - ended_at
# 	cmd3="ls -al /data/*/* --time-style full-iso | cut -d ' ' -f 6-7"
# 	exit_status3, stdout3, stderr3 = shell.exec_command(cmd3, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status3), str(stdout3), str(stderr3)))
	
# 	#4. 각 파일 내용 확인하기 - idc, zone
# 	cmd4=f"file_cnt=$({cmd1} | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep orig_master_host $file_path | head -1;echo '_';cnt=$((cnt+1));done"
# 	exit_status4, stdout4, stderr4 = shell.exec_command(cmd4, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status4), str(stdout4), str(stderr4)))
	
# 	#5. 각 파일 내용 확인하기 - issue_detail
# 	cmd5=f"file_cnt=$({cmd1} | grep failover.err | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | grep failover.err | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep HealthCheck $file_path | head -1;echo '_';cnt=$((cnt+1));done"
# 	exit_status5, stdout5, stderr5 = shell.exec_command(cmd5, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status5), str(stdout5), str(stderr5)))	

# 	#6. 각 파일 내용 확인하기 - result
# 	cmd6=f"file_cnt=$({cmd1} | grep -e failover -e switch | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$({cmd1} | grep -e failover -e switch | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);grep -A 2 -e 'Switch Report' -e 'Failover Report' $file_path | tail -1;echo '_';cnt=$((cnt+1));done"
# 	exit_status6, stdout6, stderr6 = shell.exec_command(cmd6, "deploy")
# 	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status6), str(stdout6), str(stderr6)))	

# ### 가져온 데이터 파싱
# ### columns=[manager, service_name, issue_type, issue_detail, logfile, started_at, ended_at, created_at, zone, idc, result]
# 	# manager, service_name, issue type, logfile 4개
# 	parsed_enter=stdout1.split('\n') 
# 	parsed1=[]
# 	for i in parsed_enter:
# 		eli=re.split('[.]', i)
# 		parsed1.append(eli)

# 	# started_at
# 	tmp=stdout2.split('\n')
# 	parsed2=[]
# 	for i in tmp:
# 		if len(i)==1:
# 			continue
		
# 		if i[0]=='_':
# 			parsed2.append(i.lstrip('_'))
# 		else:
# 			parsed2.append(i)

# 	# ended_at
# 	tmp=stdout3.split('\n')
# 	parsed3=[]
# 	for i in tmp:
# 		eli1=i.split()
# 		eli2=eli1[0]+' '+eli1[1].split('.')[0]
# 		parsed3.append(eli2)

# 	# idc, zone
# 	tmp=stdout4.split('\n')
# 	parsed4=[]
# 	for i in tmp:
# 		if len(i)==1:
# 			continue
# 		parsed4.append(i)

# 	hosts=[]
# 	for i in parsed4:
# 		tmp=i.split()
# 		for j in tmp:
# 			if "--orig_master_host" in j:
# 				hosts.append(j.split('=')[1].split('.')[0])
# 				break

# 	# issue_detail
# 	tmp=stdout5.split('\n')
# 	parsed5=[]
# 	for i in tmp:
# 		if len(i)==1:
# 			continue
# 		parsed5.append(i)

# 	issue_details=[]
# 	for i in range(len(parsed5)):
# 		if "SSH" in parsed5[i] and "is reachable" in parsed5[i]:
# 			issue_details.append("mysql")
# 		else:
# 			issue_details.append("OS/Network")

# 	# result
# 	tmp=stdout6.split('\n')
# 	parsed6=[]
# 	for i in tmp:
# 		if len(i)==1:
# 			continue
# 		parsed6.append(i)

# 	results=[]
# 	for i in range(len(parsed6)):
# 		if "succeeded" in parsed6[i]:
# 			results.append("succeed")
# 		else:
# 			results.append("failure")
# 	print(parsed6)


# ### 파싱 데이터 db에 저장
# 	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
# 	for i in range(len(parsed1)):
# 		manager, service_name, logfile, issue_type, result, started_at, issue_detail, ended_at, zone, idc=parsed1[i][1], parsed1[i][0], parsed_enter[i], parsed1[i][4], "none", parsed2[i], "none", parsed3[i], "none", "none"
# 		# if len(parsed1[i])>5:
# 		# 	result=parsed1[i][5]
# 		if "_" in parsed1[i][4]:
# 			issue_type=parsed1[i][4].split('_')[0]

# 		#추가 파싱 - started_at
# 		tmp1=started_at.split()
# 		months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# 		for j in range(len(months)):
# 			if months[j] in tmp1[1]:
# 				tmp1[1]=j+1
# 				break
# 		tmp1=list(map(str, tmp1))
# 		if len(tmp1[1])==1:
# 			tmp1[1]='0'+tmp1[1]
# 		started_at=tmp1[4]+"-"+tmp1[1]+"-"+tmp1[2]+" "+tmp1[3]
		
# 		#추가 파싱 - idc, zone
# 		idc_zone=get_ims_info_by_host_name(hosts[i]).json()
# 		zone=idc_zone['results'][0]['zone_name']
# 		idc=idc_zone['results'][0]['loc_b']
# 		if zone=="":
# 			zone="none"

# 		#추가 파싱 - result
# 		result_cnt=0
# 		if issue_type=="switch" or issue_type=="failover": # failover_completes는 따로 있음
# 			result=results[result_cnt]
# 			result_cnt+=1

# 		#추가 파싱 - issue_detail
# 		failover_err_cnt=0
# 		if issue_type=="failover" and result=="failure": # failover_completes는 따로 있음
# 			issue_detail=issue_details[failover_err_cnt]
# 			failover_err_cnt+=1

# 		query =f'insert into metadata(manager, service_name, logfile, issue_type, result, started_at, issue_detail, ended_at, zone, idc) values("{manager}", "{service_name}", "{logfile}", "{issue_type}", "{result}", "{started_at}",  "{issue_detail}", "{ended_at}", "{zone}", "{idc}")'
# 		ret=dbconn.execdml(query) # 0, 1

# 	lastday=workday
# 	return ret





















### 전체 서비스에 reporting
@app.get('/lumos/report_all', tags=["all_information"])
def read_all():
	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
	query = 'select * from metadata'
	result = dbconn.execsql(query)

	metadatas=[]
	for row in result :	
		data=schema.createSchemaModel(id=1, manager="_", service_name="_", issue_type="_", issue_detail="_", logfile="_", started_at="1900-01-01 00:00:00", ended_at="1900-01-01 00:00:00",  created_at="1900-01-01 00:00:00", zone="_", idc="_", result="_").dict()
		data["id"], data["manager"], data["service_name"], data["issue_type"], data["issue_detail"], data["logfile"], data["started_at"], data["ended_at"], data["created_at"], data["zone"], data["idc"], data["result"]=row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]
		metadatas.append(data)

	return metadatas





















### 기간별 장애유형 조회
@app.get('/lumos/report_custom', tags=["report_custom"])
def read_customed(service_name: Optional[str]="%", issue_type: Optional[str]="%", issue_detail:Optional[str]="%", started_at:Optional[str]="%", zone:Optional[str]="%", idc:Optional[str]="%", result:Optional[str]="%"):
	ret=()

	cols=["service_name", "issue_type", "issue_detail", "zone", "idc", "result"]
	options=[service_name, issue_type, issue_detail, zone, idc, result]
	ops_selected, cols_selected=[], []
	for i in range(len(options)):
		if options[i]!="%":
			ops_selected.append(options[i])
			cols_selected.append(cols[i])

	size=len(cols_selected)
	if "~" in started_at: # 쿼리인자가 연속 범위로 들어왔을 때
		started_range=started_at.split("~")
		started_at_start=started_range[0].strip()
		started_at_end=started_range[1].strip()		

		dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
		
		query="select "
		for i in range(size):
			query+=cols_selected[i]						
			query+=", "
		query+="count(*)"
		query+=f" from metadata where service_name like '{service_name}' and issue_type like '{issue_type}' and issue_detail like '{issue_detail}' and zone like '{zone}' and idc like '{idc}' and result like '{result}' and started_at between '{started_at_start}' and '{started_at_end}'"

		if size>0:
			query+=" group by "
		for i in range(size):
			query+=cols_selected[i]						
			if i==size-1:
				continue
			query+=", "
		print(query)
		ret+=dbconn.execsql(query)
		
	print(ret)
	metadatas=[]
	for i in ret:
		row={}
		for j in range(size):
			row[cols_selected[j]]=i[j]
		row["count"]=i[size]
		metadatas.append(row)
	print(metadatas)

	return metadatas




















# @app.post('/v1/mysql/schema/{service_id}/create', tags=["Work"])
# def schema_create(service_id:int, CallDataSet:schema.createSchemaModel) :
# 	schema_dict = CallDataSet.dict()
# 	workday = datetime.datetime.today().strftime("%Y%m%d")
# 	Log = Logger("./logs/{}.log".format(workday), 0)
# 	Log.write_log(3, "[LUMOS][Create][{}] Call Received\n\t{}\n".format(service_id, str(schema_dict)))
# 	#code, result, output = create_schema(service_id, schema_dict, Log)
# 	#return retJSON(code, result, output)
# 	return True












if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))