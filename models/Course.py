from pydantic import BaseModel

class Course(BaseModel):
    name: str
    title: str
    description: str
    url: str
    module: int
    chapter: int
    category: str
    status: str