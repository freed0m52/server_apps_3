import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials
from dotenv import load_dotenv
import secrets

from database import get_db_connection, init_db
from models import User, UserRegister, TodoCreate, TodoUpdate, TodoResponse
from auth import (
    fake_users_db, user_roles, hash_password, verify_password,
    authenticate_user, create_jwt_token, get_current_user,
    auth_user_dependency, pwd_context, security_basic
)
from rbac import require_role, Role, has_permission
from rate_limiter import limiter, rate_limit_exceeded_handler

load_dotenv()

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "secret123")

init_db()

from slowapi.errors import RateLimitExceeded

@asynccontextmanager
async def lifespan(app: FastAPI):
    if "testuser" not in fake_users_db:
        fake_users_db["testuser"] = {
            "username": "testuser",
            "hashed_password": pwd_context.hash("testpass")
        }
        user_roles["testuser"] = Role.USER
    
    if "admin" not in fake_users_db:
        fake_users_db["admin"] = {
            "username": "admin",
            "hashed_password": pwd_context.hash("adminpass")
        }
        user_roles["admin"] = Role.ADMIN
    
    if "guestuser" not in fake_users_db:
        fake_users_db["guestuser"] = {
            "username": "guestuser",
            "hashed_password": pwd_context.hash("guestpass")
        }
        user_roles["guestuser"] = Role.GUEST
    
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

def verify_docs_auth(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

if MODE == "DEV":
    from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
    from fastapi.openapi.utils import get_openapi
    
    @app.get("/docs", include_in_schema=False, dependencies=[Depends(verify_docs_auth)])
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")
    
    @app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(verify_docs_auth)])
    async def get_open_api_endpoint():
        return JSONResponse(get_openapi(title="FastAPI API", version="1.0.0", routes=app.routes))
    
elif MODE == "PROD":
    pass
else:
    raise ValueError(f"Invalid MODE value: {MODE}. Use DEV or PROD")

@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def register(request: Request, user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    hashed = hash_password(user.password)
    
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed
    }
    user_roles[user.username] = Role.USER
    
    return {"message": "New user created"}

@app.get("/login")
async def login_get(user: dict = Depends(auth_user_dependency)):
    return {"message": f"Welcome, {user['username']}!"}

@app.post("/login")
@limiter.limit("5/minute")
async def login_post(request: Request, user_data: User):
    if user_data.username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )
    
    access_token = create_jwt_token(user_data.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected_resource")
async def protected_resource(current_user: str = Depends(get_current_user)):
    return {"message": "Access granted"}

@app.get("/admin/resource")
async def admin_resource(current_user: str = Depends(require_role([Role.ADMIN]))):
    return {"message": f"Welcome admin {current_user}! You have full access."}

@app.get("/user/resource")
async def user_resource(current_user: str = Depends(require_role([Role.ADMIN, Role.USER]))):
    return {"message": f"Welcome {current_user}! You can read and update resources."}

@app.get("/guest/resource")
async def guest_resource(current_user: str = Depends(require_role([Role.ADMIN, Role.USER, Role.GUEST]))):
    return {"message": f"Welcome {current_user}! You have read-only access."}

@app.post("/admin/create")
async def admin_create_resource(current_user: str = Depends(require_role([Role.ADMIN]))):
    return {"message": f"Resource created by admin {current_user}"}

@app.put("/user/update/{resource_id}")
async def user_update_resource(resource_id: int, current_user: str = Depends(require_role([Role.ADMIN, Role.USER]))):
    return {"message": f"Resource {resource_id} updated by {current_user}"}

@app.delete("/admin/delete/{resource_id}")
async def admin_delete_resource(resource_id: int, current_user: str = Depends(require_role([Role.ADMIN]))):
    return {"message": f"Resource {resource_id} deleted by admin {current_user}"}

@app.post("/register-sqlite", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def register_sqlite(request: Request, user: UserRegister):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (user.username, user.password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
    return {"message": "User registered successfully!"}

@app.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
            (todo.title, todo.description)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
    
    return TodoResponse(id=row["id"], title=row["title"], description=row["description"], completed=bool(row["completed"]))

@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
    
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    return TodoResponse(id=row["id"], title=row["title"], description=row["description"], completed=bool(row["completed"]))

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, todo: TodoUpdate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
            (todo.title, todo.description, 1 if todo.completed else 0, todo_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        
        cursor.execute("SELECT id, title, description, completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
    
    return TodoResponse(id=row["id"], title=row["title"], description=row["description"], completed=bool(row["completed"]))

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    return {"message": "Todo deleted successfully"}

import sqlite3