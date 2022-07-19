from pydantic import BaseModel

class createSchemaModel(BaseModel):
	schema_name : str
	collation : str
