import sqlite3
from datetime import date, datetime
from mcp.server.fastmcp import FastMCP
import atexit
from utils import makedate, makedate2, getID
from db_handler import DatabaseHandler

# --- Database Handler ---



db_handler = DatabaseHandler()

# --- FastMCP Server Initialization ---

mcp = FastMCP("server_insert")

# --- MCP Tools ---

@mcp.tool()
def ApplyLeave(fromdate: str, tilldate: str, leave_type: str, emp_id:str,reason: str = "") -> str:
    """
Submits a leave application for an employee.
Inputs:
    - fromdate (str): Starting date for your leave application in "dd/mm/yyyy" format. [Required]
    - tilldate (str): Ending date for your leave applicaation "dd/mm/yyyy" format. [Required]
    - leave_type (str): Type of leave (e.g. EL: Emergency Leave, PL: Privilege Leave, LOP: Leave without Pay, CL: Comp-off Leave) [Required]
"""

    try:
        date1 = datetime.strptime(fromdate, "%d/%m/%Y")
        date2 = datetime.strptime(tilldate, "%d/%m/%Y")
        days = (date2 - date1).days + 1
    except ValueError:
        return "Invalid date format. Use dd/mm/yyyy."

    today = date.today()
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT "PL Balance", "CL Balance", "EL Balance" FROM Leave_Balance WHERE "Employee ID" = ?;',
            (emp_id,)
        )
        result = cursor.fetchone()
    finally:
        cursor.close()

    if not result:
        return "Leave balance information not found."

    if (leave_type == 'PL' and result['PL Balance'] < days) or \
       (leave_type == 'CL' and result['CL Balance'] < days) or \
       (leave_type == 'EL' and result['EL Balance'] < days):
        return "Leave application cannot be submitted. Insufficient leave balance."

    cursor = db_handler.cursor()
    fromdate_db = makedate(fromdate)
    tilldate_db = makedate(tilldate)
    try:
        cursor.execute(
            '''INSERT INTO Leave_Application 
               ("Employee ID", "FROM DATE", "TILL DATE", "LEAVE TYPE", "DAY(S)", "APPLIED", "STATUS") 
               VALUES (?, ?, ?, ?, ?, ?, ?);''',
            (emp_id, fromdate_db, tilldate_db, leave_type, days, today.strftime("%Y-%m-%d"), "Pending")
        )
        cursor.execute(
            '''UPDATE Leave_Balance 
               SET "PL Balance" = "PL Balance" - ?, 
                   "CL Balance" = "CL Balance" - ?, 
                   "EL Balance" = "EL Balance" - ? 
               WHERE "Employee ID" = ?;''',
            (
                days if leave_type == 'PL' else 0,
                days if leave_type == 'CL' else 0,
                days if leave_type == 'EL' else 0,
                emp_id
            )
        )
        db_handler.commit()
        return (
            "Leave application submitted successfully. Your leave balance is updated.\n"
            f"PL Balance: {result['PL Balance']}, "
            f"CL Balance: {result['CL Balance']}, "
            f"EL Balance: {result['EL Balance']}"
        )
    except Exception as e:
        db_handler.rollback()
        return f"Error submitting leave: {str(e)}"
    finally:
        cursor.close()

@mcp.tool()
def MakeAttendanceApplication(date: str, punchtype: str, punch_time: str, reason: str,emp_id) -> str:
    """
Submits an attendance correction or regularization application.
Inputs:
    - date (str): Date of attendance in "dd/mm/yyyy" format. [Required]
    - punchtype (str): Type of punch (e.g. Punch-In, Punch-Out, Break-In, Break-Out). [Required]
    - punch_time (str): Time of the punch ("HH:MM" format). [Required]
    - reason (str): Reason for the application. [Optional]
"""
    try:
        date_str = makedate2(date)
    except Exception:
        return "Invalid date format. Please use dd/mm/yyyy."

    tempStatus = "Initiated"
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            '''INSERT INTO Attendance_Application 
               ("Employee ID", "AppliedDate", "Punch Type", "Punch Time", "Reason", "Status") 
               VALUES (?, ?, ?, ?, ?, ?);''',
            (emp_id, date_str, punchtype, punch_time, reason, tempStatus)
        )
        db_handler.commit()
        return "Attendance application submitted."
    except Exception as e:
        db_handler.rollback()
        return f"Error submitting attendance application: {str(e)}"
    finally:
        cursor.close()

@mcp.tool()
def MakeTravelApplication(fromdate: str, todate: str, travel_type: str, purpose: str, advance: float, expense: float,emp_id) -> str:
    """
Submits a new travel application for an employee. Do not proceed until all the details are filled.
Inputs:
    - fromdate (str):Starting Date Of Travel. [Required]
    - todate (str): When to return to office again?. [Required]
    - travel_type (str): Please specify the type of travel.(eg. Outstation, local) [Required]
    - purpose (str): Purpose of the travel. [Required]
    - advance (float): Amount of advance requested. [Required]
    - expense (float): Estimated expense for the travel. [Required]
"""

    today = date.today()
    try:
        date1 = datetime.strptime(fromdate, "%d/%m/%Y")
        date2 = datetime.strptime(todate, "%d/%m/%Y")
        days = (date2 - date1).days + 1
    except Exception:
        return "Invalid date format. Please use dd/mm/yyyy."

    cursor = db_handler.cursor()
    try:
        cursor.execute('SELECT "Ref.No" FROM Travel_Application ORDER BY "Ref.No" DESC LIMIT 1')
        last_ref = cursor.fetchone()
        Ref_no = last_ref[0] + 1 if last_ref else 1

        cursor.execute(
            '''INSERT INTO Travel_Application 
               ("Employee ID", "From Date", "To Date", "Travel Type", "No. of Days", "PurposeOfTravel", "Advance", "Expense", "Applied Date", "Ref.No") 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''',
            (emp_id, makedate(fromdate), makedate(todate), travel_type, days, purpose, advance, expense, today.strftime("%Y-%m-%d"), Ref_no)
        )
        db_handler.commit()
        return "Travel application created successfully."
    except Exception as e:
        db_handler.rollback()
        return f"Error submitting travel application: {str(e)}"
    finally:
        cursor.close()

@mcp.tool()
def MakeTimeSheetEntry(date: str, hour: float, client: str, project: str,emp_id) -> str:
    """ 
Creates a timesheet entry for an employee for a specific date.
Inputs:
    - date (str): Date of the timesheet entry in "dd/mm/yyyy" format. [Required]
    - hour (float): Number of hours worked on the date. [Required]
    - client (str): Client for which Employee is working. [Required]
    - project (str): project on which Employee is working.[Required]
"""
    
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            '''INSERT INTO TimeSheet_Entry 
               ("Employee ID", "Requested Date", "Total Hour", "Client", "Project") 
               VALUES (?, ?, ?, ?, ?);''',
            (emp_id, date, hour, client, project)
        )
        db_handler.commit()
        return "Time sheet entry recorded Successfully."
    except Exception as e:
        db_handler.rollback()
        return f"Error recording time sheet entry: {str(e)}"
    finally:
        cursor.close()

@mcp.tool()
def MakeLoanApplication(loan_type: str, amount: float, installment: str,emp_id) -> str:
    """
Submits a loan application for an employee.
Inputs:
    - loan_type (float): Ask for type of loan(e.g. home,car,personal). [Required]
    - amount (float): Amount of the loan. [Required]
    - installment (str): Number of installments for repayment. [Required].
"""


    today = date.today()
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT "Bank Account No" FROM Employee_Summary WHERE EmployeeId = ?;',
            (emp_id,)
        )
        account_row = cursor.fetchone()
        account_no = account_row[0] if account_row else None

        cursor.execute(
            '''INSERT INTO Loan 
               ("Employee ID", "LoanType", "LoanDate", "AccountNo.", "AmountRequested", "NO. of Installments") 
               VALUES (?, ?, ?, ?, ?, ?);''',
            (emp_id, loan_type, today.strftime("%Y-%m-%d"), account_no, amount, installment)
        )
        db_handler.commit()
        return "Loan application submitted Successfully."
    except Exception as e:
        db_handler.rollback()
        return f"Error submitting loan application: {str(e)}"
    finally:
        cursor.close()

@mcp.tool()
def Raise_Helpdesk_Ticket(subject: str, sub_subject: str, message: str,emp_id) -> str:
    """
Raises a helpdesk ticket by collecting subject, sub-subject, and message.
Inputs:
    - subject (str): Main category of the issue (e.g., HRMS, Ticket Type 1). [Required]
    - sub_subject (str): Sub-category related to the subject (e.g., Leave Application). [Required]
    - message (str): Detailed description or content of the request. [Required]
Returns:
    - str: Confirmation message of ticket creation.
"""
    creation_date = date.today().strftime("%Y-%m-%d")
    ticket_status = "Open"
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            '''INSERT INTO Helpdesk 
               ("Employee ID", "Subject", "SubSubject", "Message", "CreationDate", "TicketStatus") 
               VALUES (?, ?, ?, ?, ?, ?);''',
            (emp_id.strip(), subject, sub_subject, message, creation_date, ticket_status)
        )
        db_handler.commit()
        return (
            f"Helpdesk ticket successfully created.\n"
            f"Subject: {subject}\nSubSubject: {sub_subject}\nStatus: {ticket_status}\nCreated On: {creation_date}"
        )
    except Exception as e:
        db_handler.rollback()
        return f"Error creating helpdesk ticket: {str(e)}"
    finally:
        cursor.close()

# --- Cleanup on Exit ---
atexit.register(db_handler.close)

# --- Main Entrypoint ---

if __name__ == "__main__":
    mcp.run(transport='stdio')
