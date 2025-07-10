import atexit
from typing import Union
from mcp.server.fastmcp import FastMCP
from utils import makedate, makedate2
from db_handler import DatabaseHandler

# --- FastMCP Server Initialization ---

mcp = FastMCP("server_read")

# --- Database Handler ---

db_handler = DatabaseHandler()



# --- MCP Tools ---

@mcp.tool()
def ViewLeaveBalance(emp_id: str) -> dict:
    """
    Retrieves the current leave balance for a given employee without any arguments.
    """

    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT "PL Balance", "CL Balance", "EL Balance" FROM Leave_Balance WHERE "Employee ID" = ?;',
            (emp_id.strip(),)
        )
        result = cursor.fetchone()
        if not result:
            return {"error": "No leave balance found for this employee."}
        return f"""
Please find below leave balance data as on today:
Privilege Leave : {result["PL Balance"]}
Comp-Off Leave : {result["CL Balance"]}
Emergency Leave : {result["EL Balance"]}
"""
    finally:
        cursor.close()


@mcp.tool()
def ViewAttendanceApplication(fromdate: str, enddate: str, emp_id) -> Union[str, dict]:
    """
Retrieves attendance application records for an employee.

Args:
    - fromdate (str): Start date in "dd/mm/yyyy" format.
    - enddate (str): End date in "dd/mm/yyyy" format.
    """
    if not fromdate and not enddate:
        return {"error": "Please provide fromdate and enddate."}

    query = (
        'SELECT "Employee ID", "AppliedDate", "Punch Type", "Punch Time", "Reason", "Status" '
        'FROM Attendance_Application WHERE "Employee ID" = ?'
    )
    params = [emp_id.strip()]

    if fromdate and enddate:
        query += ' AND "AppliedDate" BETWEEN ? AND ?'
        params.extend([makedate2(fromdate), makedate2(enddate)])
    elif fromdate:
        query += ' AND "AppliedDate" >= ?'
        params.append(makedate2(fromdate))
    elif enddate:
        query += ' AND "AppliedDate" <= ?'
        params.append(makedate2(enddate))

    cursor = db_handler.cursor()
    try:
        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        if not result:
            return {"message": "No attendance application records found for the given filters."}
        
        for row in result:
            tool_str += f"""
Applied Date: {row["AppliedDate"]}
Punch Type: {row["Punch Type"]}
Punch Time: {row["Punch Time"]}
Reason: {row["Reason"]}
Status: {row["Status"]}
            """
        
        return f"""
Attendance application records retrieved successfully.
applications:
{tool_str}
            """
    finally:
        cursor.close()


@mcp.tool()
def ViewLoanApplication(emp_id) -> Union[list, dict]:
    """
Retrieves loan application records for an employee.
    """

    query = 'SELECT * FROM Loan WHERE "Employee ID" = ?'
    params = [emp_id]

    cursor = db_handler.cursor()
    try:
        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        if not result:
            return {"error": "Loan application not found."}
        
        for row in result:
            tool_str += f"""
Loan Type: {row["Loan Type"]}
Applied Date: {row["Applied Date"]}
Amount: {row["Amount"]}
Status: {row["Status"]}
            """

        return f"""Loan application retrieved successfully.
applications:
{tool_str}
        """
    finally:
        cursor.close()


@mcp.tool()
def ViewLeaveApplication(start_date: str, end_date: str, emp_id) -> list:
    """
Show leave applications for a specific employee within a date range.
Args:
    -start_date (str): Start date in "dd/mm/yyyy" format.
    -end_date (str): End date in "dd/mm/yyyy" format.
"""

    query = 'SELECT * FROM Leave_Application WHERE "Employee ID" = ?'
    params = [emp_id]

    if start_date:
        query += ' AND "FROM DATE" >= ?'
        params.append(makedate(start_date))
    if end_date:
        query += ' AND "TILL DATE" <= ?'
        params.append(makedate(end_date))

    cursor = db_handler.cursor()
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not rows:
            return f"""
Leave applications not found for given dates.
"""
        tool_str = ""
        for row in rows:
            tool_str += f"""
Leave Type: {row["Leave Type"]}
From Date: {row["FROM DATE"]}
Till Date: {row["TILL DATE"]}
Status: {row["Status"]}
            """
        return f"""Your Leave applications retrieved successfully.
applications:
{tool_str}
        """
    finally:
        cursor.close()


@mcp.tool()
def ViewAttendancerecords(
    start_date: str, end_date: str,emp_id
) -> list|dict:
    """
Retrieves attendance records for an employee over a specified date range.
Args:
    -start_date (str): Start date in "dd/mm/yyyy" format. [Required]
    -end_date (str): End date in "dd/mm/yyyy" format. [Required]
"""
    
    if not start_date and not end_date:
        return [{"error": "Please provide start date and end date."}]


    query = 'SELECT * FROM Attendance_Regularization WHERE "Employee ID" = ?'
    params = [emp_id]

    if start_date and end_date:
        query += ' AND "Date" BETWEEN ? AND ?'
        params.extend([makedate(start_date), makedate(end_date)])
    elif start_date:
        query += ' AND "Date" >= ?'
        params.append(makedate(start_date))
    elif end_date:
        query += ' AND "Date" <= ?'
        params.append(makedate(end_date))

    cursor = db_handler.cursor()
    try:
        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        if not result:
            return [{"error": "No attendance records found."}]
        
        for row in result:
            tool_str += f"""    
Date: {row["Date"]}
In Time: {row["In Time"]}
Out Time: {row["Out Time"]}
Status: {row["Status"]}
            """

        return f"""Attendance records retrieved successfully.
records:
{tool_str}
        """
    finally:
        cursor.close()


@mcp.tool()
def ViewTravelApplication(
    emp_id, start_date = None, end_date = None
) -> list | dict:
    """
Retrieves travel application records for an employee.
Args:
    -start_date (str): Start date in "dd/mm/yyyy" format. [Optional]
    -end_date (str): End date in "dd/mm/yyyy" format. [Optional]
"""
    if not (start_date or end_date):
        return {
            "error": "Please provide either start date or end date to search travel applications."
        }

    params = []
    query = 'SELECT * FROM Travel_Application WHERE 1=1'

    params.append(emp_id)

    if start_date and end_date:
        query += ' AND "Applied Date" BETWEEN ? AND ?'
        params.extend([makedate(start_date), makedate(end_date)])
    elif start_date:
        query += ' AND "Applied Date" >= ?'
        params.append(makedate(start_date))
    elif end_date:
        query += ' AND "Applied Date" <= ?'
        params.append(makedate(end_date))

    cursor = db_handler.cursor()
    try:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        if not rows:
            return {"error": "Travel application not found."}
        
        for row in rows:
            tool_str += f"""
Travel Type: {row["Travel Type"]}
Applied Date: {row["Applied Date"]}
From Date: {row["From Date"]}
To Date: {row["To Date"]}
Status: {row["Status"]}
            """
        return f"""Travel application retrieved successfully.
applications:
{tool_str}
        """
    finally:
        cursor.close()  

# ---Ensure DB connection is closed on exit---

atexit.register(db_handler.close)

# --- Main Entrypoint ---

if __name__ == "__main__":
    mcp.run(transport='stdio')
