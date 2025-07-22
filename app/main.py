# backend/app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from . import models, schemas, crud
from .database import engine, get_db
from .dependencies import get_current_user_from_firebase, get_current_admin_user
from .auth import get_current_user_from_firebase

app = FastAPI(
    title="Employee Attendance API",
    description="API for managing employee attendance with FastAPI, PostgreSQL, and Firebase Authentication.",
    version="1.0.0",
)

# Konfigurasi CORS
# Ini penting karena frontend akan berjalan di domain yang berbeda
origins = [
    "http://localhost:5173", # URL default Vite React dev server
    "http://127.0.0.1:5173",
    # Tambahkan URL frontend yang dideploy di sini, contoh:
    # "https://your-vercel-app.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Employee Attendance API!"}

# --- Employee Endpoints ---

@app.post("/employees/", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED)
def create_employee_api(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa membuat karyawan
):
    db_employee = crud.get_employee_by_email(db, email=employee.email)
    if db_employee:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_employee(db=db, employee=employee)

@app.get("/employees/", response_model=List[schemas.Employee])
def read_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user_from_firebase) # Semua user terautentikasi bisa melihat
):
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees

@app.get("/employees/{employee_id}", response_model=schemas.Employee)
def read_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user_from_firebase)
):
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@app.put("/employees/{employee_id}", response_model=schemas.Employee)
def update_employee_api(
    employee_id: int,
    employee: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa update karyawan
):
    db_employee = crud.update_employee(db=db, employee_id=employee_id, employee_update=employee)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_api(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa delete karyawan
):
    success = crud.delete_employee(db=db, employee_id=employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# --- Attendance Endpoints ---

@app.post("/attendances/", response_model=schemas.Attendance, status_code=status.HTTP_201_CREATED)
def create_attendance_api(
    attendance: schemas.AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user_from_firebase) # Semua user terautentikasi bisa mencatat absensi
):
    # Pastikan employee_id yang diberikan valid
    employee = crud.get_employee(db, attendance.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Jika user mencoba mencatat absensi untuk dirinya sendiri, pastikan employee_id cocok
    if not current_user.is_admin and current_user.id != attendance.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only record attendance for yourself.")

    return crud.create_attendance(db=db, attendance=attendance)

@app.get("/attendances/", response_model=List[schemas.Attendance])
def read_all_attendances_api(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa melihat semua absensi
):
    attendances = crud.get_all_attendances(db, skip=skip, limit=limit)
    return attendances

@app.get("/employees/{employee_id}/attendances/", response_model=List[schemas.Attendance])
def read_employee_attendances_api(
    employee_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user_from_firebase)
):
    # User bisa melihat absensinya sendiri atau admin bisa melihat semua absensi
    if not current_user.is_admin and current_user.id != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own attendance records.")
        
    attendances = crud.get_attendances_by_employee(db, employee_id=employee_id, skip=skip, limit=limit)
    if not attendances and crud.get_employee(db, employee_id) is None: # Cek jika karyawan tidak ada
        raise HTTPException(status_code=404, detail="Employee not found or no attendance records.")
    return attendances

@app.put("/attendances/{attendance_id}", response_model=schemas.Attendance)
def update_attendance_api(
    attendance_id: int,
    attendance: schemas.AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa update absensi
):
    db_attendance = crud.update_attendance(db=db, attendance_id=attendance_id, attendance_update=attendance)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return db_attendance

@app.delete("/attendances/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance_api(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_admin_user) # Hanya admin yang bisa delete absensi
):
    success = crud.delete_attendance(db=db, attendance_id=attendance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return {"message": "Attendance record deleted successfully"}

# Endpoint untuk mendapatkan informasi user yang sedang login
@app.get("/users/me/", response_model=schemas.Employee)
def read_users_me(current_user: models.Employee = Depends(get_current_user_from_firebase)):
    return current_user