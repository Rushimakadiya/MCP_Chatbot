from server import Server
from llm_client import LLMClient
import json
import logging
import re
from typing import Any
from datetime import datetime
from utility import speak, get_user_input,login_user

EMP_ID = ""  # Default employee ID for testing
tool_name = None
payroll_continuation = False  # Flag to indicate if the payroll process is continuing

class ChatSession:
    def __init__(self, servers: list[Server], llm_client: LLMClient) -> None:
        """Initialize the chat session with servers and LLM client."""
        self.servers: list[Server] = servers
        self.llm_client: LLMClient = llm_client
        self.tools: list[Any] = []
        self.prompt_log_file = "src\\prompt_log.jsonl"
        self.user_history: list[dict[str, str]] = []
        self.initial_tool_info = ""
        self.tool_args_cache:list[dict[str, Any]] = []


    def log_prompt(self, prompt):
        json_format = {
            "datetime": str(datetime.now()),
            "prompt": prompt
        }
        try:
            with open(self.prompt_log_file, "a") as jsonl_file:
                jsonl_file.write(json.dumps(json_format) + "\n")
        except Exception as e:
            print(f"[Prompt Logging Error]: {e}")

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")
    
    async def start(self,emp_id) -> None:
        global EMP_ID, tool_name
        EMP_ID = emp_id

        try:
            for server in self.servers:
                try:
                    await server.initialize()
                    print(f"Server {server.name} initialized successfully.")
                except Exception as e:
                    print(f"Failed to initialize server {server.name}: {e}")
                    continue

            all_tools = []
            for server in self.servers:
                tools = await server.list_tools()
                all_tools.extend(tools)
            
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    # "inputSchema": tool.input_schema
                } for tool in all_tools
            ]
            for tool in self.tools:
                self.initial_tool_info += f"""
Tool_name: {tool["name"]}
Description: {tool["description"].strip().splitlines()[0]}
"""
            print("\nType 'quit' to exit.")
            print("Type 'clear' to clear history and start new chat.")
            print("Type 'logout' to logout and switch user.")
            tool_name = None


            while True:
                query = get_user_input("\n Query: ").strip()
                if query.lower() == 'quit':
                    return "quit"
                elif query == 'logout':
                    print("\nLogged out successfully!")
                    return
                
                elif query.lower() == "clear":
                    self.user_history = []
                    print("[History cleared]")
                    continue 
                elif query == "":
                    print("[Empty query, please enter a valid query]")
                    continue

                await self.process_query(query)
        finally:
            await self.cleanup_servers()   

            
    async def process_query(self, query) -> None:
        check_query_call = True
        global EMP_ID, tool_name, payroll_continuation
        
        if self.user_history:
            self.log_prompt(self.user_history)
            summary_msg = [{
                "role": "system",
                "content": f"Summarize this text pointwise (do not remove important argument inputs given by user): {json.dumps(self.user_history, indent=2)}"
            }]
            self.log_prompt(summary_msg)
            Summarized_text =  self.llm_client.get_summary(summary_msg)
            cleaned_text = re.sub(r'<think>.*?</think>\s*', '', Summarized_text, flags=re.DOTALL)
            
            self.user_history=[
                {
                    "role":"system",
                    "content":f"Summary of Previous conversation: {cleaned_text.strip()}"
                }
            ]

        self.user_history.append({"role": "user", "content": query})
        print()
        

        while True:

#------First LLM Call-----#

            if not tool_name or tool_name.get("tool") == "None":
                initial_prompt = [f"""
You are a helpful assistant with access to these tools:
{self.initial_tool_info}"
You will be provided with a user query and you will respond with ONLY the name of appropriate tool that can be used to solve user query.
If no tool description matches the user query, take tool_name as 'None' strictly nothing else.
IMPORTANT: When you need to use a tool or not, you must ONLY respond with exact JSON format as shown below and nothing else:
{{
    "tool": "tool-name"
}}
Only use tool_name from the list of tools provided above.
If user query requires more than one tool, you must respond only with the tool_name that is most relevant to the query or the tool_name that is needed to be executed first."""
                    
                ]
                self.history1 = [{"role": "system", "content": initial_prompt[0]}]

                first_message = self.history1 + self.user_history
                self.log_prompt(first_message)
                llm_response = self.llm_client.get_response(first_message)
                cleaned_text = re.sub(r'<think>.*?</think>\s*', '', llm_response, flags=re.DOTALL)
                json_str = re.search(r"\{.*\}", cleaned_text, re.DOTALL).group()
                tool_name = json.loads(json_str)
                check_query_call = False
                payroll_continuation = True

#------Check User Query Call-----#

            if check_query_call is True:
                check_query_prompt = """
You are a helpful assistant with access to the current user query and a summary of the previous conversation.

Your task is to determine whether the current user query continues the previous conversation **with the same goal**, or shifts to a new one.

Check each of the following:

1. Is the user directly answering a question the assistant just asked?
2. Is the user continuing with the **same task or tool** (e.g., continuing a form or completing missing inputs)?
3. Has the **goal of the conversation changed**, even if the topic is similar (e.g., from “applying leave” to “checking balance”)?

Rules:
- If the user **changes their intent**, e.g., from applying for leave to checking leave balance, even though both are in the same topic (“leave”), the query is **not a match**.
- Match = same task + same tool + same intent
- Do not rely on keyword overlap. Understand the user's goal.

Return **only** the following exact JSON format:

```json
{
  "query_match": "True" or "False",
  "reason": "Short explanation for your decision"
}
"""
                check_query = [{"role": "system", "content": check_query_prompt}] + self.user_history
                # check_query = [{"role": "system", "content": check_query_prompt[0]}] + llm3_response
                self.log_prompt(check_query)
                llm2_response = self.llm_client.get_response(check_query)
                # print(f"LLM: {llm2_response}")
                cleaned_text = re.sub(r'<think>.*?</think>\s*', '', llm2_response, flags=re.DOTALL)
                json_str = re.search(r"\{.*\}", cleaned_text, re.DOTALL).group()
                query_check = json.loads(json_str)
                payroll_continuation = False
                if 'false' in str(query_check["query_match"]).lower():
                    check_query_call = False 
                    tool_name = None
                    continue

            if not tool_name or tool_name.get("tool") == "None":
                tool_names = []
                for tool in self.tools:
                    tool_names.append(tool["name"])
                tool_list = "\n".join(f"- {name}" for name in tool_names)
                without_tool_prompt = f"""
We are Here to assist you with the following applications:\n
-{tool_list}\n
Please Provide your query below.
"""  
                speak(without_tool_prompt)
                # print(f"LLM_output: {without_tool_prompt}")  
    
                return           
                    
#------Getting Tool Arguments-----#

            tool_str = ""
            for tool in self.tools:
                if tool_name["tool"] == tool["name"]:
                    tool_str = f"""
Tool_name: {tool["name"]}
Description: {tool["description"]}
                    """
                    break

#------LLM Response for Tool Arguments-----#

            Instruction_prompt = (f"""You are a helpful assistant designed to extract tool arguments based on the user's input and prior conversation.
Here is the tool information:
{tool_str}
To help you with today's date is {datetime.now().strftime('%d/%m/%Y')} if required.
Your task:
-Extract as many required arguments as possible from the user's input and the summary of the conversation.
-If the user requests data for "last month", automatically set the date range from the 1st to the last day of the previous month.
- STRICTLY PROHIBITED: Never invent or assume values for missing arguments (even as examples).
- REQUIRED BEHAVIOR: If any required argument is missing, respond ONLY with a concise question to collect the missing input (e.g., "Please specify the ....").
-After collecting all required arguments, rephrase the extracted data into a concise confirmation question for the user.
-After user confirms his inputs, respond with ONLY the following exact JSON format (no explanation, no extra words):

```json
{{
    "tool": "tool-name",
    "arguments": {{
        "argument-name": "value"
    }}
}}
Additionally, if the user provides a date in any format, convert it to the format 'dd/mm/yyyy' before including it in the arguments.
Important:  
- Do not show your thought process or explain your reasoning to the user.
- Do not repeat or paraphrase the user's inputs.
- Only ask for required arguments, one at a time, in a concise manner.
Here is a summary of the user's input and prior conversation:
""")

            Instructions = [
                {
                    "role": "system",
                    "content": Instruction_prompt
                }
            ]
            self.log_prompt(Instructions + self.user_history)
            llm3_response = self.llm_client.get_response(Instructions+ self.user_history)
           
            result = await self.process_llm_response(llm3_response, tool_name)

            if result != llm3_response:
                if tool_name != "PayrollProcess":
                    tool_name = None
       
                # print(f"LLM_output: {result}")
                speak(result)
                copy_result = f"The tool '{tool_name}' was called and returned: {result}"
                self.user_history.append({"role": "assistant", "content": copy_result})
                return
            
            cleaned_text = re.sub(r'<think>.*?</think>\s*', '', llm3_response, flags=re.DOTALL)
            # print(f"LLM_output: {cleaned_text}")
            speak(cleaned_text)
            self.user_history.append({"role": "assistant", "content": cleaned_text})
            return
            

    async def process_llm_response(self, llm_response: str,tool_name) -> str:
     
        global EMP_ID, payroll_continuation

        try:
            cleaned_text = re.sub(r'<think>.*?</think>\s*', '', llm_response, flags=re.DOTALL)
            match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if match:
                json_str = match.group()
                tool_call = json.loads(json_str)
                tool_call["arguments"].update({"emp_id": EMP_ID})
                if payroll_continuation is True:
                    tool_call["arguments"].update({"stop_flag": "True"})
                # tool_name = tool_call["tool"]
                # tool_args = {k: str(v) for k, v in tool_call["arguments"].items()}
                tool_name = tool_call.get("tool", None)

                # tool_call = json.loads(llm_response)
                if "tool" in tool_call and "arguments" in tool_call:
                    logging.info(f"Executing tool: {tool_call['tool']}")
                    logging.info(f"With arguments: {tool_call['arguments']}")

                    for server in self.servers:
                        tools = await server.list_tools()
                        if any(tool.name == tool_call["tool"] for tool in tools):
                            try:
                                result = await server.execute_tool(
                                    tool_call["tool"], tool_call["arguments"]
                                )

                                if isinstance(result, dict) and "progress" in result:
                                    progress = result["progress"]
                                    total = result["total"]
                                    percentage = (progress / total) * 100
                                    logging.info(
                                        f"Progress: {progress}/{total} ({percentage:.1f}%)"
                                    )

                                return f"Tool execution result: {result}"
                            except Exception as e:
                                error_msg = f"Error executing tool: {str(e)}"
                                logging.error(error_msg)
                                return error_msg

                    return f"No server found with tool: {tool_call['tool']}"
            return llm_response
        except json.JSONDecodeError:
            return llm_response
