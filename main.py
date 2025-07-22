# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time, datetime

from database import engine, Base, get_db
from models import Employee, Attendance # Import models untuk memastikan tabel dibuat
import schemas
import crud

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Buat tabel di database (akan dijalankan saat aplikasi startup)
# Ini hanya untuk development. Untuk production, gunakan Alembic atau migrasi database yang lebih formal.
Base.metadata.create_all(bind=engine)

# Endpoint untuk Karyawan
@app.post("/employees/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud.create_employee(db=db, employee=employee)

@app.get("/employees/", response_model=List[schemas.Employee])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees

@app.get("/employees/{employee_id}", response_model=schemas.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

# Endpoint untuk Absensi
@app.post("/attendances/", response_model=schemas.Attendance)
def create_attendance(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    # Cek apakah karyawan ada
    employee = crud.get_employee(db, employee_id=attendance.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Cek apakah sudah ada absensi masuk untuk tanggal yang sama
    existing_attendance = crud.get_today_attendance_by_employee(db, attendance.employee_id, attendance.date)
    if existing_attendance and existing_attendance.check_out is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee already checked in for today and hasn't checked out."
        )
    elif existing_attendance and existing_attendance.check_out is not None:
        # Jika sudah check-in dan check-out, bisa anggap ini absensi baru atau error jika aturan hanya 1x per hari
        # Untuk kasus ini, kita akan melarang absensi baru jika sudah check-in dan check-out untuk tanggal yang sama.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee already completed attendance for today."
        )

    return crud.create_attendance(db=db, attendance=attendance)

@app.put("/attendances/{attendance_id}/checkout", response_model=schemas.Attendance)
def update_attendance_checkout(attendance_id: int, check_out_time: time, db: Session = Depends(get_db)):
    db_attendance = crud.get_attendance(db, attendance_id=attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if db_attendance.check_out is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already checked out.")

    updated_attendance = crud.update_attendance_checkout(db=db, attendance_id=attendance_id, check_out_time=check_out_time)
    if not updated_attendance:
        raise HTTPException(status_code=400, detail="Failed to update check-out.")
    return updated_attendance

@app.get("/attendances/", response_model=List[schemas.Attendance])
def read_attendances(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    attendances = crud.get_attendances(db, skip=skip, limit=limit)
    return attendances

@app.get("/attendances/employee/{employee_id}", response_model=List[schemas.Attendance])
def read_attendances_by_employee(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    attendances = crud.get_attendances_by_employee_id(db, employee_id, start_date, end_date)
    if not attendances and crud.get_employee(db, employee_id) is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return attendances