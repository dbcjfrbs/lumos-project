from ast import Pass
from importlib.metadata import metadata
from itertools import count
import json
from ssl import Options
from threading import excepthook
import uvicorn
import fastapi
from datetime import date, datetime
from model import schema_api_model as schema
from util.Logger import *
from util.ExecSSH import *
from util.MysqlConnector import *
from fastapi_utils.tasks import repeat_every
import re
from typing import Optional
from util.func import *
import os

app = fastapi.FastAPI()

### 전체 metadata 조회
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


















### 일단 vip 기반 mha 구성한 거에서 로직 짜고 있음
### mha manager에 접속 및 switch shell script 실행
@app.get('/lumos/switch_call', tags=["switch_call"])
def switch_call():
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	
	shell = ExecSSH(host='mha-practice.ay1.krane.9rum.cc', user='deploy', logger=Log)

	cmd=f"masterha_master_switch --master_state=alive --conf=/etc/masterha/app1.cnf --new_master_host=slave-practice --interactive=0 2> /dev/null"
	exit_status, stdout, stderr = shell.exec_command(cmd, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))
	if "gtid inconsistency" in stdout:
		return "switching is failed.\n because gtid inconsistency problem."
	elif "known_hosts inconsistency" in stdout:
		return "switching is failed.\n because known_hosts inconsistency."
	elif "long query locked problem" in stdout:
		return "switching is failed.\n because long query locked problem."
	else:
		return "switching is succeeded.\n"


@app.get('/lumos/gtid_check', tags=["gtid_check"])
def gtid_check():
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	
	dbconn1 = MysqlConnector('master-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')
	dbconn2 = MysqlConnector('slave-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')

	query1="show slave status;"
	ret=dbconn1.execsql(query1)
	
	query2="show variables like 'server_uuid';"
	master_uuid=""
	if len(ret)==0:
		master_uuid=dbconn1.execsql(query2)[0][1]
	else:
		master_uuid=dbconn2.execsql(query2)[0][1]
	
	query3="show variables like 'gtid_executed';"
	gtid_sets1=sorted(dbconn1.execsql(query3)[0][1].split(','))
	gtid_sets2=sorted(dbconn2.execsql(query3)[0][1].split(','))	
	size=len(gtid_sets1)
	for i in range(size):
		if master_uuid in gtid_sets1[i]: # 현재 업데이트 되고 있는 gtid에 대해서 대량 쿼리로 인해 master, slave 간 동기화 상태가 불일치하는 상황은 예외처리 해주기
			continue
		if gtid_sets1[i]!=gtid_sets2[i]:
			return 0
	return 1


# ssh 접속 전에 hosts 정보 삭제하도록 함
@app.get('/lumos/known_hosts_check', tags=["known_hosts_check"])
def known_hosts_check():
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	

	# os.system("sed '/master-practice/d' /home/deploy/.ssh/known_hosts")
	# os.system("sed '/slave-practice/d' /home/deploy/.ssh/known_hosts")
	os.system("sed -i '' '/master-practice/d' ~/.ssh/known_hosts")
	os.system("sed -i '' '/slave-practice/d' ~/.ssh/known_hosts")

	return "known_hosts information deleted."


# locked_long_query
@app.get('/lumos/locked_long_query_check', tags=["locked_long_query_check"])
def locked_long_query_check():
	now = datetime.datetime.today()
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	
	dbconn = MysqlConnector('slave-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')

	# blocking query(롱쿼리)가 시작된 시간 조회
	query="select trx_started from information_schema.innodb_trx where trx_state='RUNNING' and trx_query is null order by trx_started;"
	ret=dbconn.execsql(query)[0][0]
	now=datetime.datetime.today()
	if now-ret>datetime.timedelta(seconds=100):
		return 0
	return 1


if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	# uvicorn.run(app, host="192.168.0.17", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))