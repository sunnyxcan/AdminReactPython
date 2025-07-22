# crud.py

from sqlalchemy.orm import Session
from typing import List, Optional
from models import Employee, Attendance
from schemas import EmployeeCreate, AttendanceCreate
from datetime import date, time, datetime

# Employee CRUD
def get_employee(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.id == employee_id).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    db_employee = Employee(name=employee.name, position=employee.position)
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

# Attendance CRUD
def get_attendance(db: Session, attendance_id: int):
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()

def get_attendances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Attendance).offset(skip).limit(limit).all()

def get_attendances_by_employee_id(db: Session, employee_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None):
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    return query.all()

def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(
        employee_id=attendance.employee_id,
        date=attendance.date,
        check_in=attendance.check_in,
        check_out=attendance.check_out
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance_checkout(db: Session, attendance_id: int, check_out_time: time):
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if db_attendance:
        db_attendance.check_out = check_out_time
        db_attendance.updated_at = datetime.now()
        db.commit()
        db.refresh(db_attendance)
    return db_attendance

def get_today_attendance_by_employee(db: Session, employee_id: int, current_date: date):
    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date == current_date
    ).first()