from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
import uvicorn
from starlette.responses import Response
from server_read import mcp as mcp_read
from server_insert import mcp as mcp_insert
from payroll import mcp as mcp_payroll
from Admin import mcp as mcp_admin

def create_starlette_app(debug: bool = False) -> Starlette:
    sse_read = SseServerTransport("/read/messages/")
    sse_insert = SseServerTransport("/insert/messages/")
    sse_payroll = SseServerTransport("/payroll/messages/")
    sse_admin = SseServerTransport("/admin/messages/")

    async def handle_sse_read(request: Request) -> None:
        async with sse_read.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await mcp_read._mcp_server.run(read_stream, write_stream, mcp_read._mcp_server.create_initialization_options())
        return Response()

    async def handle_sse_insert(request: Request) -> None:
        async with sse_insert.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await mcp_insert._mcp_server.run(read_stream, write_stream, mcp_insert._mcp_server.create_initialization_options())
        return Response()
    
    async def handle_sse_payroll(request: Request) -> None:
        async with sse_read.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await mcp_payroll._mcp_server.run(read_stream, write_stream, mcp_payroll._mcp_server.create_initialization_options())
        return Response()
    
    async def handle_sse_admin(request: Request) -> None:
        async with sse_read.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await mcp_admin._mcp_server.run(read_stream, write_stream, mcp_admin._mcp_server.create_initialization_options())
        return Response()
    
    return Starlette(
        debug=debug,
        routes=[
            Route("/read/sse", endpoint=handle_sse_read),
            Mount("/read/messages/", app=sse_read.handle_post_message),
            Route("/insert/sse", endpoint=handle_sse_insert),
            Mount("/insert/messages/", app=sse_insert.handle_post_message),
            Route("/payroll/sse", endpoint=handle_sse_payroll),
            Mount("/payroll/messages/", app=sse_payroll.handle_post_message),
            Route("/admin/sse", endpoint=handle_sse_admin),
            Mount("/admin/messages/", app=sse_admin.handle_post_message),
        ],
    )

if __name__ == "__main__":
    starlette_app = create_starlette_app(debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)