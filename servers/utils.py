from db_handler import DatabaseHandler
from datetime import datetime

db_handler = DatabaseHandler()

def fromdate(date_str: str) -> str:
    fromdate = date_str + "-01" + " 00:00:00"
    return fromdate

def Todate(date_str: str) ->  str:
    todate = date_str + "-31" + " 00:00:00"
    return todate

def makedate(date_str: str) -> str:
    """Convert date from 'dd/mm/yyyy' to 'yyyy-mm-dd' format."""
    day, month, year = date_str.split('/')
    return f"{year}-{month}-{day}"

def makedate2(date_str: str) -> str:
    """Convert date from 'dd/mm/yyyy' to 'yyyy-mm-dd 00:00:00' format."""
    day, month, year = date_str.split('/')
    return f"{year}-{month}-{day} 00:00:00"

def makemonth(month: str) -> str:
    """Convert month from 'MM-YYYY' to 'YYYY-MM' format."""
    formatted_month = datetime.strptime(month,"%B").month
    return f"{formatted_month:02d}"

def getID(name: str) -> str:
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT EmployeeId FROM Employee_Summary WHERE FirstName LIKE ?',
            (f"%{name}%",)
        )
        result = cursor.fetchone()
        if result:
            return result["EmployeeId"]
        raise ValueError(f"Employee with name '{name}' not found.")
    finally:
        cursor.close()

def getname(emp_id: str) -> str:
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT FirstName FROM Employee_Summary WHERE EmployeeId = ?',
            (emp_id,)
        )
        result = cursor.fetchone()
        if result:
            return f"""{result["FirstName"]}"""
        raise ValueError(f"Employee with ID '{emp_id}' not found.")
    finally:
        cursor.close()