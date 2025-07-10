
from mcp.server.fastmcp import FastMCP
import atexit
from collections import defaultdict
from db_handler import DatabaseHandler
from utils import Todate, fromdate, makemonth
# --- Database Handler ---

db_handler = DatabaseHandler()
atexit.register(db_handler.close)

mcp = FastMCP("Payroll")

flag1,flag2,flag3,flag4,flag5,flag6,flagch = False,False,False,False,False,False,False

# --- MCP Tools ---


#----Step-1: Payroll Process ----#
@mcp.tool()
def NewJoineesAndSeperated(month: str, year: str, category_type: str, category: str) -> dict:
    """
        Fetches the count of new joinees and separated employees for a given month and department.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    PayrollMonth = year + "-" + makemonth(month)
    cursor = db_handler.cursor()
    try:
        cursor = db_handler.cursor()
        query = f"SELECT COUNT(*) FROM Employee_Summary WHERE {category_type} = ?"
        cursor.execute(query, (category,))
        result = cursor.fetchone()
        cursor.execute(
            f'SELECT COUNT(*) FROM Employee_Summary WHERE DOJ >= ? AND {category_type} = ?',
            (PayrollMonth, category)
        )
        new_joinees = cursor.fetchone()[0]

        cursor.execute(
            f'SELECT COUNT(*) FROM Employee_Summary WHERE DOL <= ? AND {category_type} = ?',
            (PayrollMonth, category)
        )
        separated = cursor.fetchone()[0]
        global flag2,flag3,flag4,flag5,flag6
        flag2,flag3,flag4,flag5,flag6 = False,False,False,False,False
        
        return f"""
please confirm the below details for Payroll Process:
Total Employees : {result[0]},
New Joinees : {new_joinees},
Separated Employees : {separated}
        """
    
    finally:
        cursor.close()

#----Step-2: Payroll Process ----#

@mcp.tool()
def DataApproval(month: str, Year: str, category_type: str, category: str) -> dict:
    """
        Fetches the summary of data approval status for employees in a given month and department.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    PayrollMonth = Year + "-" + makemonth(month)
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            f'SELECT * FROM Employee_Summary WHERE {category_type} = ? AND (DOJ <= ? AND (DOL IS NULL OR DOL >= ?))',
            (category, PayrollMonth, PayrollMonth)
        )
        rows = cursor.fetchall()
        total = len(rows)

        # Bank
        bank_unapproved = bank_missing = 0
        # PF/ESIC
        pf_unapproved = pf_missing = 0
        # Aadhaar
        aadhaar_unapproved = aadhaar_missing = 0

        for row in rows:
            # Bank
            bank_value = row["Bank Account No"]
            bank_status = row["Bank Account No Status"]
            if not bank_value:
                bank_missing += 1
            elif bank_status == "Unapproved":
                bank_unapproved += 1

            # PF/ESIC
            pf_value = row["ESIC No"]
            pf_status = row["ESIC Status"]
            if not pf_value:
                pf_missing += 1
            elif pf_status == "Unapproved":
                pf_unapproved += 1

            # Aadhaar
            aadhaar_value = row["Aadhaar No"] if "Aadhaar No" in row.keys() else None
            if not aadhaar_value:
                aadhaar_missing += 1
            elif "Unapproved" in str(aadhaar_value):
                aadhaar_unapproved += 1
        global flag3,flag4,flag5,flag6
        flag3,flag4,flag5,flag6 = False,False,False,False
        return f"""
please confirm Bank,PF/ESIC and Aadhaar details for Payroll Process:
Total Employees: {total},
Bank Details: {bank_unapproved} Unapproved, {bank_missing} Missing,
PF/ESIC Details: {pf_unapproved} Unapproved, {pf_missing} Missing,
Aadhaar Details: {aadhaar_unapproved} Unapproved, {aadhaar_missing} Missing
"""

    finally:
        cursor.close()

#----Step-3: Payroll Process ----#

@mcp.tool()
def SalaryProcessForPayroll(month: str, Year: str, category_type: str, category: str) -> dict:
    """
        Fetches the summary of salary processing status for a given month and department.
        This function checks for missing current CTC, revised salaries, and any stops in salary processing.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    PayrollMonth = Year + "-" + makemonth(month)
    cursor = db_handler.cursor()
    try:
        cursor.execute(
                'SELECT COUNT(*) FROM Salary_Master WHERE "Current CTC" IS NULL OR "Current CTC" = 0',
            )
        missing_current_ctc_count = cursor.fetchone()[0]
        cursor.execute(
                'SELECT COUNT(*) FROM Salary_Master WHERE "Previous CTC" != "Current CTC"'
            )
        revised_salary_count = cursor.fetchone()[0]
        stop_flags = ["StopBankPayment", "StopEMI", "StopSalary"]
        stops = {}
        for flag in stop_flags:
            cursor.execute(
                f'SELECT COUNT(*) FROM {flag} WHERE "From Date" >= ? AND "To Date" <= ?',
                (fromdate(PayrollMonth),Todate(PayrollMonth))
            )
            stops[flag] = cursor.fetchone()[0]
        global flag4,flag5,flag6
        flag4,flag5,flag6 = False,False,False
        # summary = {
        #     "missing_current_ctc_count": missing_current_ctc_count,
        #     "revised_salary_count": revised_salary_count,
        #     "stops": stops
        # }
        return f"""
please confirm the salary processing status for Payroll Process:
Missing Current CTC Count: {missing_current_ctc_count},
Revised Salary Count: {revised_salary_count},
Stop Bank Payment: {stops.get("StopBankPayment", 0)},
Stop EMI: {stops.get("StopEMI", 0)},
Stop Salary: {stops.get("StopSalary", 0)}
        """
    
    finally:
        cursor.close()

#----Step-4: Payroll Process ----#

@mcp.tool()
def AttendanceProcessForPayroll(month: str, Year: str, category_type: str, category: str) -> dict:
    """
        Fetches the attendance summary for a given month and department.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    PayrollMonth = Year + "-" + makemonth(month)
    pending_apps = defaultdict(list)
    pending_apps = {
        "Attendance": [],
        "Leave": [],
        "Travel": []
    }
    cursor = db_handler.cursor()
    try:
        # Attendance
        cursor.execute(
        'SELECT * FROM Attendance_Application WHERE "AppliedDate" BETWEEN ? AND ? AND "Status" = ?',
        (fromdate(PayrollMonth), Todate(PayrollMonth), "Pending")
        )
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute(
                f'SELECT "EmployeeId" from Employee_Summary WHERE "EmployeeId" = ? AND {category_type} = ?',
                (row["Employee ID"], category)
            )
            employee = cursor.fetchone()
            if employee is None:
                rows.remove(row)
                continue

            pending_apps["Attendance"].append(dict(row))

        # Leave
        cursor.execute(
        'SELECT "Leave_ID", "FROM DATE", "TILL DATE", "Leave Type", "Reason", "Status","Employee ID" FROM Leave_Application WHERE "FROM DATE" <= ? AND "TILL DATE" >= ? AND "Status" = ?',
        (fromdate(PayrollMonth), Todate(PayrollMonth), "Pending")
        )
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute(
                f'SELECT "EmployeeId" from Employee_Summary WHERE "EmployeeId" = ? AND {category_type} = ?',
                (row["Employee ID"], category)
            )
            employee = cursor.fetchone()
            if employee is None:
                rows.remove(row)
                continue
                
            pending_apps["Leave"].append(dict(row))

        # Travel
        cursor.execute(
        'SELECT * FROM Travel_Application WHERE "Applied Date" BETWEEN ? AND ? AND "Status" = ?',
        (fromdate(PayrollMonth), Todate(PayrollMonth), "Pending")
        )
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute(
                f'SELECT "EmployeeId" from Employee_Summary WHERE "EmployeeId" = ? AND {category_type} = ?',
                (row["Employee ID"], category)
            )
            employee = cursor.fetchone()
            if employee is None:
                rows.remove(row)
                continue

            pending_apps["Travel"].append(dict(row))
        global flag5,flag6
        flag5,flag6 = False,False
        if not pending_apps:
            return {"message": "No pending applications found for the given month."}
        return f"""
Pending Applications for {month} {Year}:
Attendance: {len(pending_apps["Attendance"])} applications
Leave: {len(pending_apps["Leave"])} applications
Travel: {len(pending_apps["Travel"])} applications
Please review the pending applications and confirm if you want to proceed with the payroll process.
        """
    
    finally:
        cursor.close()

#--- Step:4.5 Payroll Process ----#
@mcp.tool()
def SubmitAttendanceforPayroll(month: str, Year: str, category_type: str, category: str) -> dict:
    """
        Takes confirmation to submit attendance for payroll processing.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    return """
attendance for payroll processing is submitted successfully.
"""

#----Step-5: Payroll Process ----#
@mcp.tool()
def ArrearsAndAdhocs(month: str, Year: str, category_type: str, category: str) -> dict:
    """
        Fetches the summary of arrears and adhoc payments for a given month and department.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    PayrollMonth = Year + "-" + makemonth(month)
    cursor = db_handler.cursor()
    try:
        cursor.execute(
            'SELECT * FROM Arrear WHERE "Arrear From Date" >= ?  AND "Arrear Till Date" <= ?',
            (fromdate(PayrollMonth), Todate(PayrollMonth))
        )
        arrears = cursor.fetchall()
        cursor.execute(
            'SELECT * FROM Adhoc WHERE Month = ? AND Year = ?',
            (month, Year)
        )
        adhocs = cursor.fetchall()
        filtered_arrears = []
        for arrear in arrears:
            cursor.execute(
                f'SELECT * FROM Employee_Summary WHERE EmployeeId = ? AND {category_type} = ?',
                (arrear["Employee ID"],category)
            )
            employee = cursor.fetchone()
            if employee is not None:
                filtered_arrears.append(dict(arrear))
        
        filtered_adhocs = []
        for adhoc in adhocs:
            cursor.execute(
                f'SELECT * FROM Employee_Summary WHERE EmployeeId = ? AND {category_type} = ?',
                (adhoc["Employee ID"],category)
            )
            employee = cursor.fetchone()
            if employee is not None:
                filtered_adhocs.append(dict(adhoc))
        global flag6
        flag6 = False
        return f"""
please confirm the Arrears and Adhoc payments for Payroll Process:
Arrears: {len(filtered_arrears)} records found.
Adhoc Payments: {len(filtered_adhocs)} records found.
        """
    
    finally:
        cursor.close()

#----Step-6: Payroll Process ----#

@mcp.tool()
def ShowsSummaryForPayroll(month: str, Year: str, category_type: str, category: str) -> str:
    """
        Fetches the summary of salary processing for a given month and department.
        Inputs:
            - month (str): Payroll month(Eg.: January, February, March, April....) . [Required]
            - Year (str): Year for the payroll process.(Eg.: 2025) [Required]
            - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...) [Required]
            - category (str): Specific category value to filter. [Required]
    """
    global flag6
    PayrollMonth = Year + "-" + makemonth(month)
    cursor = db_handler.cursor()
    try:
        cursor.execute(
        f'SELECT * FROM StopSalary WHERE "From Date" >= ? AND "To Date" <= ?',
        (fromdate(PayrollMonth), Todate(PayrollMonth))
        )
        stop_salarys = cursor.fetchall()
        stop_salary_cnt = 0
        for stop_salary in stop_salarys:
            cursor.execute(
                    f'SELECT * FROM Employee_Summary WHERE EmployeeId = ? AND {category_type} = ?',
                    (stop_salary["Employee ID"],category)
                )
            employee = cursor.fetchone()
            if employee is not None:
                stop_salary_cnt+= 1
                
        cursor.execute(
        f'SELECT * FROM StopBankPayment WHERE "From Date" >= ? AND "To Date" <= ?',
        (fromdate(PayrollMonth), Todate(PayrollMonth))
        )
        stop_payments = cursor.fetchall()
        stop_payment_cnt = 0
        for stop_payment in stop_payments:
            cursor.execute(
                    f'SELECT * FROM Employee_Summary WHERE EmployeeId = ? AND {category_type} = ?',
                    (stop_payment["Employee ID"],category)
                )
            employee = cursor.fetchone()
            if employee is not None:
                stop_payment_cnt+= 1
        
        query = f"SELECT COUNT(*) FROM Employee_Summary WHERE {category_type} = ?"
        cursor.execute(query, (category,))
        result = cursor.fetchone()

        process_count = result[0] - stop_salary_cnt 
        flag6 = True
        # Confirm payroll processing
        return f"""
please confirm the summary for Payroll Process:
Total Employees: {result[0]},
Stop Salary Count: {stop_salary_cnt},
Stop Bank Payment Count: {stop_payment_cnt},
Payroll Process Count: {process_count}
Do you want to proceed with the payroll process for {process_count} employees?"""
    finally:
        cursor.close()

    


@mcp.tool()
def PayrollProcess(month: str, year:str, category_type: str, category:str,emp_id,stop_flag = False) -> dict:
    """
Continues the payroll process for a given month and department until process count to start payroll is achived.
Inputs:
    - month (str): Payroll month(Eg.: January, February, March, April....)[Required].
    - year (str): Year for the payroll process.(Eg.: 2025)[Required] 
    - category_type (str): Type of category to filter.(Eg.: Company,Department,Branch...)[Required] 
    - category (str): Specific category value to filter(Eg.: HR,IT,Techical,Infra...).[Required] 
    """
    PayrollMonth = year + "-" + makemonth(month)
    
    global flag1,flag2,flag3,flag4,flag5,flag6,flagch
    Confirmation_msg = "Do you want to proceed further with the Payroll Process?"

    flags = [flag1, flag2, flag3, flag4, flagch, flag5, flag6]
    
    if(stop_flag is True):
        for flag_idx in range(len(flags)):
            if flags[flag_idx] == False and flag_idx != 0:
                flags[flag_idx-1] = False
                break 


    if flag1 == False:  
        flag1 = True
        
        return f"""
{NewJoineesAndSeperated(month, year, category_type, category)}
{Confirmation_msg}
        """
    if flag2 == False:
        flag2 = True
        return f"""
{DataApproval(month, year, category_type, category)}
{Confirmation_msg}
        """
    if flag3 == False:
        flag3 = True
        return f"""
{SalaryProcessForPayroll(month, year, category_type, category)}
{Confirmation_msg}
        """
    if flag4 == False:

        flag4 = True
        return f"""
{AttendanceProcessForPayroll(month, year, category_type, category)}
{Confirmation_msg}
        """
    if flagch == False:
        flagch = True
        return f"""
{SubmitAttendanceforPayroll(month, year, category_type, category)}
{Confirmation_msg}
        """
    if flag5 == False:
        flag5 = True
        return f"""
{ArrearsAndAdhocs(month, year, category_type, category)}
        """
    if flag6 == False:
        flag6 = True
        return f"""
{ShowsSummaryForPayroll(month, year, category_type, category)}
{Confirmation_msg}
        """

    flag1, flag2, flag3, flag4, flag5, flag6,flagch = False, False, False, False, False, False, False

    return f"""
Payroll process completed successfully.
    """

# --- Cleanup on Exit ---
atexit.register(db_handler.close)

# --- Main Entrypoint ---

if __name__ == "__main__":
    
    mcp.run(transport='stdio')



