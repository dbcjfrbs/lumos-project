from pydantic import BaseModel

class createSchemaModel(BaseModel):
	schema_name : str
	collation : str

class dropSchemaModel(BaseModel):
	schema_name : str
