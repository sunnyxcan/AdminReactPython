# backend/app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas
from typing import List, Optional

def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def get_employee_by_email(db: Session, email: str):
    return db.query(models.Employee).filter(models.Employee.email == email).first()

def get_employee_by_firebase_uid(db: Session, firebase_uid: str):
    return db.query(models.Employee).filter(models.Employee.firebase_uid == firebase_uid).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: schemas.EmployeeCreate, firebase_uid: Optional[str] = None):
    db_employee = models.Employee(
        name=employee.name,
        email=employee.email,
        position=employee.position,
        firebase_uid=firebase_uid # Bisa diset saat membuat atau diupdate nanti
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employee(db: Session, employee_id: int, employee_update: schemas.EmployeeUpdate):
    db_employee = get_employee(db, employee_id)
    if db_employee:
        update_data = employee_update.model_dump(exclude_unset=True) # Hanya update field yang disertakan
        for key, value in update_data.items():
            setattr(db_employee, key, value)
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, employee_id: int):
    db_employee = get_employee(db, employee_id)
    if db_employee:
        db.delete(db_employee)
        db.commit()
        return True
    return False

def get_attendance(db: Session, attendance_id: int):
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

def get_attendances_by_employee(db: Session, employee_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Attendance).filter(models.Attendance.employee_id == employee_id).offset(skip).limit(limit).all()

def get_all_attendances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Attendance).offset(skip).limit(limit).all()

def create_attendance(db: Session, attendance: schemas.AttendanceCreate):
    db_attendance = models.Attendance(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance(db: Session, attendance_id: int, attendance_update: schemas.AttendanceUpdate):
    db_attendance = get_attendance(db, attendance_id)
    if db_attendance:
        update_data = attendance_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_attendance, key, value)
        db.add(db_attendance)
        db.commit()
        db.refresh(db_attendance)
    return db_attendance

def delete_attendance(db: Session, attendance_id: int):
    db_attendance = get_attendance(db, attendance_id)
    if db_attendance:
        db.delete(db_attendance)
        db.commit()
        return True
    return False