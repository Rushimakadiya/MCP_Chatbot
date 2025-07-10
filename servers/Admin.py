from mcp.server.fastmcp import FastMCP
import atexit
from db_handler import DatabaseHandler
from utils import getID, getname,makemonth

#------Initialize FastMCP server

mcp = FastMCP("Admin")

db_handler = DatabaseHandler()


@mcp.tool()
def get_employee_details(emp_id,employee_name: str = None) -> dict:
    """
    Retrieve the details of employees, using username given for authorization.
    Inputs:
        employee_name (str): Name of a specific employee.[Optional]
    """
    cursor = db_handler.cursor()
    username = getname(emp_id)
    try:
        # If username is same as employee_name (or employee_name is None), show user's own details
        if employee_name is None or username.lower() == employee_name.lower():
            cursor.execute(
                'SELECT * FROM Employee_Summary WHERE "FirstName" LIKE ?',
                (f"%{username}%",)
            )
            result = cursor.fetchone()

       
        cursor.execute(
            'SELECT * FROM Employee_Summary WHERE "Manager" LIKE ?',
            (f"%{username}%",)
        )
        emp_rows = cursor.fetchall()
        if not emp_rows:
            return f"""
You are not authorized to view employee details or no employees found under your management.
            """
        emp_ids = [row["EmployeeId"] for row in emp_rows]

        # If employee_name is provided, check if that employee is under this manager
        if employee_name:
            try:
                emp_id = getID(employee_name)
            except ValueError as e:
                return f"""
{str(e)}
                """
            if emp_id not in emp_ids:
                return f"""
This employee is not under your management.
                """
            emp_ids = [emp_id]

        placeholders = ','.join('?' for _ in emp_ids)
        query = f'SELECT * FROM Employee_Summary WHERE "EmployeeId" IN ({placeholders})'
        params = emp_ids
        cursor.execute(query, params)
        result = cursor.fetchall()

        if result:
            tool_str = ""
            for row in result:
                tool_str += f"""
EmployeeID: {row["EmployeeId"]},
FirstName: {row["FirstName"]},
LastName: {row["LastName"]},
Job Title: {row["JobTitle"]},
Gender: {row["Gender"]},
Date of Birth: {row["Date of Birth"]},
Department: {row["Department"]},
Joining Date: {row["DOJ"]},
"""
            return f"""
Employee details retrieved successfully.
Details:
{tool_str}
            """
        else:
            return f"""
No employee details found.
"""
    finally:
        cursor.close()


@mcp.tool()
def get_employee_salary(name: str, emp_id: str) -> dict:
    """
    Retrieve the salary details of the specified employee name or user's own salary details.
    Inputs:
        name (str): Name of the employee to retrieve salary details for. If not provided, defaults to the username.
    """
    cursor = db_handler.cursor()
    try:
        username= getname(emp_id)
        cursor.execute(
            'SELECT * FROM Employee_Summary WHERE "FirstName" LIKE ?',
            (f"%{username}%",)
        )
        result = cursor.fetchone()

        adm_id = result["EmployeeId"]
        if (adm_id == 'EMPZ001' or username == name):
            emp_id = getID(name)
            query = 'SELECT * FROM Salary_Master WHERE "Employee ID" = ?'
            cursor.execute(query, (emp_id.strip(),))
            result = cursor.fetchone()

            if result:
                return f"""
Employee ID: {result["Employee ID"]},
Employee Name: {getname(result["Employee ID"])},
Previous CTC: {result["Previous CTC"]},
Current CTC: {result["Current CTC"]},
WEF: {result["WEF"]},
                """
            else:
                return f"""
Salary details not found
"""
        else:
            return f"""
You are not authorized to view salary details.
"""
    finally:
        cursor.close()


@mcp.tool()
def Show_Employee_Performance(employee_name: str, emp_id: str) -> dict:
    """
    Retrieve performance review details of employee .
    The manager can view all reviews under them, or only for a specific employee under them.
    Inputs:
        employee_name (str): Name of a specific employee under the manager.
    """
    cursor = db_handler.cursor()
    username = getname(emp_id)
    try:
        cursor.execute(
            'SELECT "EmployeeId" FROM Employee_Summary WHERE "Manager" LIKE ?',
            (f"%{username}%",)
        )
        emp_rows = cursor.fetchall()
        emp_ids = [row["EmployeeId"] for row in emp_rows]

        if not emp_ids:
            return f"""
You are not authorized to view performance reviews or no employees found under your management.
"""

       
        if employee_name:
            try:
                emp_id = getID(employee_name)
            except ValueError as e:
                return f"""
{str(e)}
"""
            if emp_id in emp_ids or username.lower() == employee_name.lower():
                emp_ids = [emp_id]
            else:
                return  f"""
This employee is not under your management.
"""

        placeholders = ','.join('?' for _ in emp_ids)
        query = f'SELECT * FROM "PMSGoals&Review" WHERE "Employee ID" IN ({placeholders})'
        params = emp_ids
        cursor.execute(query, params)
        result = cursor.fetchall()

        if result:
            for row in result:
                tool_str = f"""
Employee ID: {row["Employee ID"]},
Employee Name: {getname(row["Employee ID"])},
Achievement: {row["Achivement"]},
Remarks: {row["Remarks"]},
"""

            return f"""
Performance reviews retrieved successfully.
Details:
{tool_str}
"""
        else:
            return f"""
No performance reviews found for the specified date range."""
    finally:
        cursor.close()
        

@mcp.tool()
def Show_All_Pending_Leaves_For_Month(month, Year,emp_id) -> dict:
    """
    Show all pending leave applications for every employee for the specified month and year.
    Only accessible by admin or authorized manager.
    Inputs:
        - month (str): Payroll month(Eg.: January, February, March, April....) . 
        - Year (str): Year for the payroll process.(Eg.: 2025) 
    """
    month_num = makemonth(month)  # returns '03' for March
    year_int = int(Year)
    month_int = int(month_num)
    from_date = f"{year_int}-{month_num}-01"
    if month_int == 12:
        till_date = f"{year_int + 1}-01-01"
    else:
        till_date = f"{year_int}-{month_int + 1:02d}-01"

    cursor = db_handler.cursor()
    try:
        query = '''
            SELECT * FROM Leave_Application
            WHERE "STATUS" = 'Pending'
            AND "FROM DATE" > ?
            AND "TILL DATE" <= ?
            ORDER BY "Employee ID", "FROM DATE"
        '''
        cursor.execute(query, (from_date, till_date))
        rows = cursor.fetchall()
        if not rows:
            return {"message": "No pending leave applications found for the specified month."}

        tool_str = ""
        for row in rows:
            tool_str += f"""
Leave ID: {row["Leave_ID"]},
Employee ID: {row["Employee ID"]},
Employee Name: {getname(row["Employee ID"])},
FROM DATE: {row["FROM DATE"]},
TILL DATE: {row["TILL DATE"]},
STATUS: {row["STATUS"]},
"""
           
        return f"""
Pending leave applications for {month} {Year}:
{tool_str}
        """
    finally:
        cursor.close()


@mcp.tool()
def Update_Leave_Application_Status(leave_id: int, status: str, emp_id ) -> dict:
    """
Approve a leave application by its ID, using provided emp_id for authorization.
Inputs:
    status (str): New status for the leave application (e.g., 'Approved', 'Rejected').
    leave_id (int): ID of the leave application to approve.
    """
    cursor = db_handler.cursor()
    username = getname(emp_id)
    try:
        cursor.execute(
            'SELECT "Employee ID" FROM Leave_Application WHERE "Leave_ID" = ?',
            (leave_id,)
        )
        leave_row = cursor.fetchone()
        if not leave_row:
            return f"""Leave application not found."""
        employee_id = leave_row["Employee ID"]

        cursor.execute(
            'SELECT "Manager" FROM Employee_Summary WHERE "EmployeeId" = ?',
            (employee_id,)
        )
        emp_row = cursor.fetchone()
        if not emp_row:
            return f"""Employee not found.
"""
        manager_name = emp_row["Manager"]

        if username.lower() != manager_name.lower():
            return f"""
You are not authorized to approve this leave application."""

        query = 'UPDATE Leave_Application SET "STATUS" = ? WHERE "Leave_ID" = ?'
        cursor.execute(query, (status, leave_id))
        db_handler.commit()
        return f"""
Leave application Status Updated successfully.
"""
    finally:
        cursor.close()


atexit.register(db_handler.close)

if __name__ == "__main__":
    mcp.run(transport='stdio')














   