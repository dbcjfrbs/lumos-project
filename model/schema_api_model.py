from pydantic import BaseModel

class createSchemaModel(BaseModel):
	id: int
	service: str
	created_at: str
	error_code: str
