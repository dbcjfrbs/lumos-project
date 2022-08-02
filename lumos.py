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


if __name__ == '__main__':
	print("================= LUMOS Start : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))
	uvicorn.run(app, host="0.0.0.0", debug=True, port=4321)
	print("================= LUMOS End : {} =================".format(datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")))