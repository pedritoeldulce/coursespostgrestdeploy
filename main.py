from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from fastapi.responses import JSONResponse
import jwt
import psycopg2
from psycopg2 import extras
from config_postgres import config_postgres

from models.Course import Course

app = FastAPI()


def get_connection():
    try:
        params = config_postgres()
        conn = psycopg2.connect(**params)
        return conn

    except (Exception, psycopg2.DatabaseError) as error:
        return print(error)


""" @app.middleware("http")
async def root(request:Request, call_next):
    print(f"Accessing the route: {request.url}")
    response = await call_next(request)
    return response """
    

# credenciales
users = [{
    "username": "noacanoa",
    "password": "1234"
}]


async def verify_token(token: str):
    
    data = jwt.decode(token, "noacanoa", algorithms="HS256")

    for user in users:
        if user['username'] == data['username'] and user['password'] == data['password']:
            return True
            
    return False

# Nota: Falta agregar la exception de token incorrecto. cuando cambio el token se cae el api


@app.post("/login")
async def login(username: str, password: str):
    for user in users:
        if user['username'] == username and user['password'] == password:
            return jwt.encode(user, "noacanoa", algorithm="HS256")
    return JSONResponse(status_code=400, content={"message": "Bad Credentials"})


@app.get("/courses")
async def get_courses(authorization: str = Header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Im5vYWNhbm9hI"
                                                  "iwicGFzc3dvcmQiOiIxMjM0In0.I4dzLcC4IyEgL3JmIEYLsE_m6Wd5OpdK8C7jIlF"
                                                  "zMqw")):

    authorized = await verify_token(authorization)

    if authorized:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("SELECT * FROM courses")
        courses_found = cur.fetchall()
        cur.close()

        if conn is not None:
            conn.close()
        
        return JSONResponse(status_code=200, content={"courses": courses_found})

    return JSONResponse(status_code=400, content={"message": "unautorized"})


@app.get('/courses/{id}')
async def get_course(id: int, authorization: str = Header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZ"
                                                          "SI6Im5vYWNhbm9hIiwicGFzc3dvcmQiOiIxMjM0In0.I4dzLc"
                                                          "C4IyEgL3JmIEYLsE_m6Wd5OpdK8C7jIlFzMqw")):
    authorized = await verify_token(authorization)

    if authorized:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute('SELECT * FROM courses WHERE id = %s', (id,))
        course_founded = cur.fetchone()

        cur.close()

        if conn is not None:
            conn.close()

        if course_founded is None:
            return JSONResponse(status_code=404, content={"message": "course not found"})

        return JSONResponse(status_code=200, content={"message": "course found", "course": course_founded})

    return JSONResponse(status_code=400, content={"message": "unautorized"})


@app.post("/courses")
async def create_course(course: Course, authorization: str = Header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZ"
                                                                    "SI6Im5vYWNhbm9hIiwicGFzc3dvcmQiOiIxMjM0In0.I4dzLc"
                                                                    "C4IyEgL3JmIEYLsE_m6Wd5OpdK8C7jIlFzMqw")):
    authorized = await verify_token(authorization)

    if authorized:
        conn = get_connection()
        cur = conn.cursor()

        # búsqueda si hay un repetido (name, url, module y chapter)
        cur.execute('SELECT name, url, module, chapter FROM courses WHERE name = %s and url = %s and module=%s  '
                    'and chapter=%s', (course.name, course.url, course.module, course.chapter))
        course_found = cur.fetchone()

        if course_found:
            raise HTTPException(status_code=400, detail={"message": "bad request"})

        else:
            cur.execute('INSERT INTO courses (name, title, description, url, module, chapter, category, status) values '
                        '(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *',
                        (course.name, course.title, course.description, course.url, course.module, course.chapter,
                         course.category, course.status))

            new_course = cur.fetchone()
            conn.commit()
            cur.close()

            if conn is not None:
                conn.close()

            return JSONResponse(status_code=201, content={"message": "courses created", "course": new_course})
    return JSONResponse(status_code=400, content={"message": "unathorized"})


@app.put("/courses/{id}")
async def update_course(id: int, course: Course, authorization: str = Header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZ"
                                                                    "SI6Im5vYWNhbm9hIiwicGFzc3dvcmQiOiIxMjM0In0.I4dzLc"
                                                                    "C4IyEgL3JmIEYLsE_m6Wd5OpdK8C7jIlFzMqw")):
    authorized = await verify_token(authorization)

    if authorized:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        cur.execute("UPDATE courses SET name=%s, title=%s, description=%s, url=%s, module=%s, chapter=%s, category=%s,"
                    "status=%s WHERE id = %s RETURNING *", (course.name, course.title, course.description, course.url,
                                                            course.module, course.chapter, course.category, course.status,
                                                            id))

        course_updated = cur.fetchone()
        conn.commit()
        cur.close()

        if conn is not None:
            conn.close()

        if course_updated is None:
            return JSONResponse(status_code=404, content={"message": "course not found"})

        return JSONResponse(status_code=200, content={"message": "course updated", "course": course_updated})

    return JSONResponse(status_code=400, content={"message": "unauthorized"})


@app.delete("/courses/{id}")
async def delete_course(id: int, authorization: str = Header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZ"
                                                             "SI6Im5vYWNhbm9hIiwicGFzc3dvcmQiOiIxMjM0In0.I4dzLc"
                                                             "C4IyEgL3JmIEYLsE_m6Wd5OpdK8C7jIlFzMqw")):

    authorized = await verify_token(authorization)

    if authorized:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("DELETE FROM courses WHERE id= %s RETURNING *", (id, ))

        course_found = cur.fetchone()
        conn.commit()

        cur.close()

        if conn is not None:
            conn.close()

        if course_found is None:
            return JSONResponse(status_code=404, content={"message": "course not found"})

        return JSONResponse(status_code=200, content={"message": "course deleted", "course": course_found})
