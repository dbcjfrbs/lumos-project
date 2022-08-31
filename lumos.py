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
from typing import List
from starlette.responses import RedirectResponse

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
def read_customed(service_name: Optional[str]="%", issue_type: Optional[str]="%", issue_detail:Optional[str]="%", zone:Optional[str]="%", idc:Optional[str]="%", result:Optional[str]="%", started_at_from:Optional[str]="%", started_at_to:Optional[str]="%"):
	# 입력값 양쪽 공백 없애기
	service_name=service_name.strip()
	issue_type=issue_type.strip()
	issue_detail=issue_detail.strip()
	zone=zone.strip()
	idc=idc.strip()
	result=result.strip()
	started_at_from=started_at_from.strip()
	started_at_to=started_at_to.strip()

	ret=()

	cols=["service_name", "issue_type", "issue_detail", "zone", "idc", "result"]
	options=[service_name, issue_type, issue_detail, zone, idc, result]

	ops_selected, cols_selected=[], []
	for i in range(len(options)):
		if options[i]!="%":
			ops_selected.append(options[i])
			cols_selected.append(cols[i])

	size=len(cols_selected)

	# db 연동 및 쿼리 생성
	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
	
	query="select "
	for i in range(size):
		query+=cols_selected[i]						
		query+=", "
	query+="count(*)"
	query+=f" from metadata where service_name like '{service_name}' and issue_type like '{issue_type}' and issue_detail like '{issue_detail}' and zone like '{zone}' and idc like '{idc}' and result like '{result}'"
	# 기간 조건 설정
	if '%' in started_at_from and '%' in started_at_to:
		pass
	elif '%' in started_at_from and '%' not in started_at_to:
		query+=f" and '{started_at_to}' >= started_at"
	elif '%' not in started_at_from and '%' in started_at_to:
		query+=f" and '{started_at_from}' <= started_at"
	else:
		query+=f" and started_at between '{started_at_from}' and '{started_at_to}'"

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





















### mha manager 접속 및 switch shell script 실행
### 대체로 만든 switch call이니 cnf에서 서버 정보를 가져오진 않음
@app.get('/lumos/switch_call', tags=["switch_call"])
def switch_call():
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")
	shell = ExecSSH(host='mha-practice.ay1.krane.9rum.cc', user='deploy', logger=Log)

	# db 연동 및 master host 획득(switching call을 master에 보내야 하기에 현 slave host를 알아야 함)
	dbconn1 = MysqlConnector('master-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')

	query1="show processlist;"
	ret=dbconn1.execsql(query1)

	slave_host="master-practice"
	for i in ret:
		if i[4]=="Binlog Dump GTID":
			slave_host="slave-practice"
			break

	cmd=f"masterha_master_switch --master_state=alive --conf=/etc/masterha/app1.cnf --new_master_host={slave_host} --interactive=0"
	exit_status, stdout, stderr = shell.exec_command(cmd, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))
	print(stdout)

	if "gtid inconsistency" in stdout:
		return "switching is failed.\n because gtid inconsistency problem."
	if "wrong ip or host" in stdout:
		return "switching is failed.\n because wrong ip or host in known_hosts file."
	if "lock issue" in stdout:
		return "switching is failed.\n because lock problem."
	if "transaction is waiting" in stdout:
		return "transaction is waiting. retry switching."
	if "query is executing" in stdout:
		return "query is executing. retry switching."
		
	return "switching is succeeded.\n"


@app.get('/lumos/gtid_check', tags=["gtid_check"])
def gtid_check():
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	

	dbconn1 = MysqlConnector('master-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')
	dbconn2 = MysqlConnector('slave-practice.ay1.krane.9rum.cc', 3306, 'analysis', 'mha', 'mha')
	query="show processlist;"

	ret1=dbconn1.execsql(query)
	ret2=dbconn2.execsql(query)

	master_uuid=""
	query1="show variables like 'server_uuid';"
	for i in ret1:
		if i[4]=="Binlog Dump GTID":
			master_uuid=dbconn1.execsql(query1)[0][1]
	for i in ret2:
		if i[4]=="Binlog Dump GTID":
			master_uuid=dbconn1.execsql(query1)[0][1]
	
	query3="show variables like 'gtid_executed';"
	gtid_sets1=sorted(dbconn1.execsql(query3)[0][1].split(','))
	gtid_sets2=sorted(dbconn2.execsql(query3)[0][1].split(','))	
	size=len(gtid_sets1)
	if len(gtid_sets1)!=len(gtid_sets2):
		return 0
	for i in range(size):
		if master_uuid in gtid_sets1[i]: # 현재 업데이트 되고 있는 gtid에 대해서 대량 쿼리로 인해 master, slave 간 동기화 상태가 불일치하는 상황은 예외처리 해주기
			continue
		if gtid_sets1[i]!=gtid_sets2[i]:
			return 0
	return 1





# mha system 각 노드에서 known_host 파일 내용 삭제 로직
# 1. mha switching script가 실행되면 mha cnf파일을 읽어 각 노드(매니저, master, slave) 호스트 명을 전부 가져옴.
# 3. known_host 점검 api를 호출할 때 각 노드 호스트명을 post방식으로 담아 호출히도록 함.(swiching 스트립트 안에서 while문을 통해 n번 반복하도록 했음)
# 4. 호출된 known_host 점검 api에서는 전달받은 호스트명을 기반으로 해당 노드에 접속해 known_hosts 파일 내용을 전부 삭제해서 해당 노드에서 다른 노드로의 잘못된 ssh 접속을 막도록 함.
@app.post('/lumos/known_hosts_check', tags=["known_hosts_check"])
def known_hosts_check(node: str):
	now = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")

	shell = ExecSSH(host=node, user='deploy', logger=Log)
	try:
		cmd=f"cat /dev/null > /home/deploy/.ssh/known_hosts"
		exit_status, stdout, stderr = shell.exec_command(cmd, "deploy")
		Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))
		return 1

	except Exception as e:
		return 0


# lock issue
# mha swiching script 파일에서 lock_issue_check api를 호출할 때 각 노드 호스트명을 전달함
# 전달한 호스트명이 마스터일 경우에 한해 밑에처럼 로직이 실행되도록 함
@app.post('/lumos/lock_issue_check', tags=["lock_issue_check"])
def locked_long_query_check(node: str):
	node=node.strip()

	now = datetime.datetime.today()
	Log = Logger("./logs/{}.log".format(now), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")	

	dbconn = MysqlConnector(node, 3306, 'analysis', 'mha', 'mha')
	query="show processlist;"
	ret=dbconn.execsql(query)

	for i in ret:
		# 만약 post를 통해 전달받은 호스트가 마스터라면 
		if i[4]=="Binlog Dump GTID":

			#query1. 트랜잭션이 락 상태에서 다른 트랜재션이 대기하고 있는 상황이 5초 이상 지속된다면 switching 실패되었다고 반환
			#    	  -  waiting_trx_started, 즉 기다리는 트랜잭션의 대기시간이 5초 이상되었을 때 실패되도록 로직 작성
			#query2. 트랜잭션 안에서 롱쿼리가 수행중인 경우 해당 롱쿼리가 5초 이상 지속된다면 switching 실패되었다고 반환
			query1="""select r.trx_started waiting_trx_started, b.trx_id blocking_trx_id, b.trx_query blocking_trx_query, r.trx_id waiting_trx_id, r.trx_query waiting_trx_query 
					from performance_schema.data_lock_waits w 
					inner join information_schema.innodb_trx b on b.trx_id=w.blocking_engine_transaction_id 
					inner join information_schema.innodb_trx r on r.trx_id=w.requesting_engine_transaction_id 
					order by b.trx_started limit 1;"""
			query2="select trx_started from information_schema.innodb_trx where trx_state='RUNNING' and trx_query is not null order by trx_started;"

			ret1=dbconn.execsql(query1)
			ret2=dbconn.execsql(query2)

			now=datetime.datetime.today()
			print(ret1)
			print(ret2)

			# 상황1, 2가 모두 아닐 경우 점검 이상 없음
			if len(ret1)==0 and len(ret2)==0:
				return 1
			# 상황 1일 경우 5초 이상이면 실패하게 하고, 5초 미만이면 "Other transaction is waiting, retry swtching." 메세지를 보내 다시 swithcing 호출하도록 권함.
			if len(ret1)!=0:
				if now-ret1[0][0]>datetime.timedelta(seconds=5):
					return 0
				else:
					return 2
			# 상황 2일 경우 10초 이상이면 실패하게 하고, 10초 미만이면 "query is executing, retry switching" 메세지를 보내 다시 swithcing 호출하도록 권함.
			if len(ret2)!=0:
				if now-ret2[0][0]>datetime.timedelta(seconds=10):
					return 0
				else:
					return 3
					# return RedirectResponse(url='switch_call', status_code=302)

	return "This host is not master."


if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	# uvicorn.run(app, host="192.168.0.17", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))