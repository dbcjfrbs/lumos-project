import json
import uvicorn
import fastapi
import datetime
import requests
from model import schema_api_model
from util.Logger import *
from util.ExecSSH import *
from fastapi_utils.tasks import repeat_every

app = fastapi.FastAPI()

## SCHEMA FUNCTION

# mha에서 주기적으로 로그 가져오는 스케줄러
@app.on_event("startup")
@repeat_every(seconds=5)
def mha_log_get():
	workday = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(workday), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")
	
	shell = ExecSSH(host='replica-slave.ay1.krane.9rum.cc', user='deploy', logger=Log)
	exit_status, stdout_list, stderr_list = shell.exec_file("/home/deploy/lumos/batch_cmd.sh")
	
	stdout=""
	stderr=""
	for i in stdout_list:
		stdout+=i
	for i in stderr_list:
		stderr+=i	

	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))	
	
	return str(stdout)

@app.get('/v1/lumos/report, tag=["Report"]')
# 나중에 mha 호스트로 변경해야 함 
def report() :
	workday = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(workday), 0)
	Log.write_log(3, "[LUMOS][Report] Call Received\n")
	#code, result, output = list_schema(service_id, Log)
	#return retJSON(code, result, output)

	shell = ExecSSH(host='replica-slave.ay1.krane.9rum.cc', user='deploy', logger=Log)
	exit_status, stdout, stderr = shell.exec_command("s", "deploy")
	Log.write_log(3, "{}, {}, {}\n".format(str(exit_status), str(stdout), str(stderr)))
	
	return True

@app.post('/v1/mysql/schema/{service_id}/create', tags=["Work"])
def schema_create(service_id:int, CallDataSet:schema_api_model.createSchemaModel) :
	schema_dict = CallDataSet.dict()
	workday = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/{}.log".format(workday), 0)
	Log.write_log(3, "[LUMOS][Create][{}] Call Received\n\t{}\n".format(service_id, str(schema_dict)))
	#code, result, output = create_schema(service_id, schema_dict, Log)
	#return retJSON(code, result, output)
	return True

if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
