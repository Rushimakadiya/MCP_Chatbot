from db_handler import DatabaseHandler
import pyttsx3
import speech_recognition as sr

db = DatabaseHandler()


async def login_user() -> list:
    
    global EMP_ID
    def getID(name: str) -> str:
        """Retrieve EmployeeId by first name."""
        cursor = db.cursor()
        try:
            cursor.execute(
                'SELECT EmployeeId FROM Employee_Summary WHERE LOWER(FirstName) LIKE ?',
                (f"%{name}%",)
            )
            employee_ID = cursor.fetchone()
            cursor.execute(
                'SELECT EXISTS(SELECT 1 FROM Employee_Summary WHERE LOWER(M' \
                'anager) = ?) AS name_exists',
                (name.lower(),)
            )
            manager_exists = cursor.fetchone()[0]
                
            if employee_ID:
                return employee_ID["EmployeeId"],manager_exists
            raise ValueError(f"Employee with name '{name}' not found in any department.")
        finally:
            cursor.close()

    while True:
        username = input("\nIn order to use our services please Enter your username: ").strip().lower()
        
        try:
            user_first_name = username.split()[0].title()
            emp_id, manager_exists = getID(user_first_name)
            EMP_ID = emp_id
            print(f"\nWelcome, {EMP_ID} - {user_first_name.capitalize()}!")
            return {"emp_id": emp_id, "manager_exists": manager_exists}
        except Exception as e:
            print("Invalid input. Please enter your username again.")



def select_servers_for_user(user_info: dict, all_server_configs: dict) -> dict:
    
    manager_exists = user_info.get("manager_exists", "0")
    emp_id = user_info.get("emp_id", "user")
    allowed = ["Insert_Queries", "Read_Queries"]
    if manager_exists: 
        while True:
            role = input("\nDo you Want to Proceed as 'Admin' or 'User'?").strip().capitalize()
            if role not in ["Admin", "User"]:
                print("Invalid role. Please enter 'Admin' or 'User'.")
                continue  
            else:
                if role == "Admin":
                    allowed = ["Admin"]
                break 

    if emp_id == "EMPZ001":
        allowed.append("Payroll")
    return {name: cfg for name, cfg in all_server_configs.items() if name in allowed}

def speak(text):
        print(text)
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 180)

        tts_engine.say(text)
        tts_engine.runAndWait()

def get_user_input(prompt="Query: "):
    print("\nType 's' to speak or just type your input and press Enter.")
    choice = input("Input mode (s = speech, Enter = text): ").strip().lower()
    if choice == 's':
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            while True:
                speak("Listening...")
                try:
                    audio = recognizer.listen(source, timeout=4) 
                    text = recognizer.recognize_google(audio)
                    print(f"You said: {text}")
                    return text
                except Exception:
                    speak("Sorry, I could not understand.Can you please repeat?")
                    continue                    
    else:
        return input(prompt)

