import asyncio
from config import Configuration
from db_handler import DatabaseHandler
from chat_session import ChatSession
from server import Server
from llm_client import LLMClient
from db_handler import DatabaseHandler
from utility import login_user, select_servers_for_user
db = DatabaseHandler()



            
# --- SELECT SERVERS BASED ON USER ROLE OR ID ---#



async def main() -> None:
    config = Configuration()
    server_config = config.load_config("servers_config_v1.json")
    user_info = await login_user()
    emp_id = user_info.get("emp_id", "user")
    selected_servers = select_servers_for_user(user_info, server_config["mcpServers"])
    servers = [
        Server(name, srv_config)
        for name, srv_config in selected_servers.items()
    ]
    llm_client = LLMClient(config.llm_api_key)
    chat_session = ChatSession(servers, llm_client)
    message = await chat_session.start(emp_id)
    await main() if message != "quit" else None

if __name__ == "__main__":
    asyncio.run(main())