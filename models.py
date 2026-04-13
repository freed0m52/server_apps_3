from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class UserRegister(BaseModel):
    username: str
    password: str

class TodoCreate(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: str
    description: str
    completed: bool

class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool