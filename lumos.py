import json
import uvicorn
import fastapi
import datetime
import requests
from model import schema_api_model
from util.Logger import *
from util.ExecSSH import *

app = fastapi.FastAPI()

## SCHEMA FUNCTION
@app.get('/v1/mysql/schema/{service_id}/list', tags=["Report"])
def schema_list(service_id:int) :
	workday = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/schema/{}.log".format(workday), 0)
	Log.write_log(3, "[Schema][List][{}] Call Received\n".format(service_id))
	#code, result, output = list_schema(service_id, Log)
	#return retJSON(code, result, output)
	return True

@app.post('/v1/mysql/schema/{service_id}/create', tags=["Work"])
def schema_create(service_id:int, CallDataSet:schema_api_model.createSchemaModel) :
	schema_dict = CallDataSet.dict()
	workday = datetime.datetime.today().strftime("%Y%m%d")
	Log = Logger("./logs/schema/{}.log".format(workday), 0)
	Log.write_log(3, "[Schema][Create][{}] Call Received\n\t{}\n".format(service_id, str(schema_dict)))
	#code, result, output = create_schema(service_id, schema_dict, Log)
	#return retJSON(code, result, output)
	return True

if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
