from fastapi import FastAPI, Request, HTTPException

from fastapi.responses import JSONResponse
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


@app.get("/courses")
async def get_courses():

    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    cur.execute("SELECT * FROM courses")
    courses_found = cur.fetchall()
    cur.close()

    if conn is not None:
        conn.close()
    
    return JSONResponse(status_code=200, content={"courses": courses_found})


@app.get('/courses/{id}')
async def get_course(id: int):

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

@app.post("/courses")
async def create_course(course: Course):

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


@app.put("/courses/{id}")
async def update_course(id: int, course: Course):
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


@app.delete("/courses/{id}")
async def delete_course(id: int):

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