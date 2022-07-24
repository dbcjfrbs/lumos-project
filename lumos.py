import json
import uvicorn
import fastapi
import datetime
import requests
from model import schema_api_model as schema
from util.Logger import *
from util.ExecSSH import *
from util.MysqlConnector import *
from fastapi_utils.tasks import repeat_every
import re
from typing import Optional

app = fastapi.FastAPI()

### mha에서 주기적으로 업데이트 된 로그만 가져오는 스케줄러 : 개발완료 되면 crontab 사용하고 아래 스케줄러는 삭제할 예정
@app.on_event("startup")
@repeat_every(seconds=60)
def batchWork():
	now = datetime.datetime.today().strftime("%H%M%S")
	workpoint = "080000" # 설정시간 0800am
	# if int(now)<int(workpoint):
	# 	return 1

	print("start up")
	workday = datetime.datetime.today().strftime("%Y%m%d") # 배치 당겨온 기록 남기기
	Log = Logger("./logs/{}.log".format(workday), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")
	
	shell = ExecSSH(host='mha-test.ay1.krane.9rum.cc', user='deploy', logger=Log)
	# exit_status, stdout_list, stderr_list = shell.exec_file("/Users/kakao/lumos-project/batch_cmd.sh") - 파일로 안하고 command로 하니까 됨 나중에 이유 알아보기
	command="s=$(echo $MHA_LOG_GET_CNT);e=$(ls -a /data/kakao1/ | wc -l);cnt=$(expr $e - $s);ls -a /data/kakao1 | tail -n $cnt;sed -i \"10s/.*/export MHA_LOG_GET_CNT=`ls -a /data/kakao1/ | wc -l`/g\" .bashrc;source .bashrc;"
	exit_status, stdout, stderr = shell.exec_command(command, "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))
	
	parsed_enter=stdout.split('\n') # 데이터 파싱
	parsed_dot=[]
	for i in parsed_enter:
		eli=re.split('[.]', i)
		parsed_dot.append(eli)

	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root') # db 연동
	for i in parsed_dot:
		service, created_at, error_code=i[0], i[3], i[4]
		if len(i)>5:
			error_code=error_code+'.'+i[5] # .err 포함
		query =f'insert into metadata(service, created_at, error_code) values("{service}", "{created_at}", "{error_code}")'
		result=dbconn.execdml(query) # 0, 1

	return result


### 전체 서비스에 reporting
@app.get('/lumos/report/all', tags=["all_service"])
def read_all():
	# workday = datetime.datetime.today().strftime("%Y%m%d")
	# Log = Logger("./logs/{}.log".format(workday), 0)
	# Log.write_log(3, "[LUMOS][Report] Call Received\n")
	#code, result, output = list_schema(service_id, Log)
	#return retJSON(code, result, output)

	# shell = ExecSSH(host='mha-test.ay1.krane.9rum.cc', user='deploy', logger=Log)
	# exit_status, stdout, stderr = shell.exec_command("s", "deploy")
	# Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))

	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
	query = 'select * from metadata'
	result = dbconn.execsql(query)

	metadatas=[]
	for row in result :	
		data=schema.createSchemaModel(id=1, service="_", created_at="_", error_code="_").dict()
		data["id"], data["service"], data["created_at"], data["error_code"]=row[0], row[1], row[2], row[3]
		metadatas.append(data)

	return metadatas


## service별 reporting
@app.get('/lumos/report/{service}', tags=["specific_service"])
def read_service(service:str):
	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
	query = f"select * from metadata where service='{service}'"
	result = dbconn.execsql(query)

	metadatas=[]
	for row in result :	
		print(row)
		data=schema.createSchemaModel(id=1, service="_", created_at="_", error_code="_").dict()
		data["id"], data["service"], data["created_at"], data["error_code"]=row[0], row[1], row[2], row[3]
		metadatas.append(data)

	return metadatas
	

### 통합 path test - 1)컬럼, 2)날짜 외 공백 처리 추가 필요
@app.get('/lumos/report_customed', tags=["customed"])
def read_customed(service: Optional[str]="%", created_at: Optional[str]="%", error_code:Optional[str]="%"):
	result=()
	failover_cnt, failover_fail, f_percent=0, 0, 0
	switching_cnt, switching_fail, s_percent=0, 0, 0
	failover, switching={},{}

	if "~" in created_at: # 쿼리인자가 연속 범위로 들어왔을 때
		created_range=created_at.split("~")
		created_at_start=created_range[0].strip()
		created_at_end=created_range[1].strip()

		dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
		query = f"select * from metadata where service like '{service}' and created_at between '{created_at_start}' and '{created_at_end}' and error_code like '{error_code}'"
		result= result+dbconn.execsql(query)
		
		# response 맨 앞에 failover 정보 추가
		query_failover = f"select count(*) as failover from metadata where error_code like '%failover%'"
		failover_cnt+=dbconn.execsql(query_failover)[0][0]
		query_failover_fail = f"select count(*) as failover from metadata where error_code like '%failover.err'"
		failover_fail+=dbconn.execsql(query_failover_fail)[0][0]
		 
	if " " in created_at: # 불연속 범위로 들어왔을 때
		created_list=created_at.split()
		for i in created_list:
			dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
			query = f"select * from metadata where service like '{service}' and created_at like '{i}' and error_code like '{error_code}'"
			result = result+ dbconn.execsql(query)

			query_failover = f"select count(*) as failover from metadata where error_code like '%failover%'"
			failover_cnt+=dbconn.execsql(query_failover)[0][0]
			query_failover_fail = f"select count(*) as failover from metadata where error_code like '%failover.err'"
			failover_fail+=dbconn.execsql(query_failover_fail)[0][0]

	# 쿼리 인자가 하나만 들어왔을 때
	dbconn = MysqlConnector('localhost', 3306, 'analysis', 'root', 'root')
	query = f"select * from metadata where service like '{service}' and created_at like '{created_at}' and error_code like '{error_code}'"
	result = result+ dbconn.execsql(query)

	query_failover = f"select count(*) as failover from metadata where error_code like '%failover%'"
	failover_cnt+=dbconn.execsql(query_failover)[0][0]
	query_failover_fail = f"select count(*) as failover from metadata where error_code like '%failover.err'"
	failover_fail+=dbconn.execsql(query_failover_fail)[0][0]

	failover["failover_total"]=failover_cnt
	failover["failover_fail"]=failover_fail
	failover["fail_percent"]=str(failover_fail/failover_cnt*100)+'%'
	metadatas=[failover]
	for row in result :	
		data=schema.createSchemaModel(id=1, service="_", created_at="_", error_code="_").dict()
		data["id"], data["service"], data["created_at"], data["error_code"]=row[0], row[1], row[2], row[3]
		metadatas.append(data)

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
	print("================= LUMOS End : {} =웅ㅇ================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))