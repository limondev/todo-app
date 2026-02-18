from fastapi import FastAPI, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional

SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TodoDB(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    completed = Column(Boolean, default=False)
    deadline = Column(DateTime, nullable=True)
    category = Column(String, default="Загальне")


Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, category: Optional[str] = None, db: Session = Depends(get_db)):
    all_categories = [c[0] for c in db.query(distinct(TodoDB.category)).all()]

    query = db.query(TodoDB)
    if category:
        query = query.filter(TodoDB.category == category)

    todos = query.order_by(TodoDB.completed.asc(), TodoDB.deadline.asc()).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "todos": todos,
        "all_categories": all_categories,
        "current_category": category
    })


@app.post("/add")
def add_todo(title: str = Form(...), deadline: Optional[str] = Form(None), category: Optional[str] = Form(None),
             db: Session = Depends(get_db)):
    dt = datetime.fromisoformat(deadline) if deadline else None
    cat = category if category and category.strip() else "Загальне"
    new_todo = TodoDB(title=title, deadline=dt, category=cat)
    db.add(new_todo)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/switch/{todo_id}")
def switch_status(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if todo:
        todo.completed = not todo.completed
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete/{todo_id}")
def delete_item(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if todo:
        db.delete(todo)
        db.commit()
    return RedirectResponse(url="/", status_code=303)