from typing import Annotated
from fastapi import APIRouter, Cookie, Query, WebSocket, WebSocketDisconnect, WebSocketException, status, Depends
from fastapi.responses import HTMLResponse
from saas_app.service.websocket import manager

router = APIRouter(prefix="/websocket", tags=["websocket"])

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`wss://miniature-space-cod-vqqwp9rwp7pfpxqq-8000.app.github.dev/websocket/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
@router.get("", include_in_schema=False)
async def get():
    return HTMLResponse(html)


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@router.websocket("/{item_id}/ws")
async def websocket_endpoint(*, websocket: WebSocket, item_id: str, q: int | None = None, cookie_or_token: Annotated[str, Depends(get_cookie_or_token)]) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Session cookie or token value: {cookie_or_token}")
            if q is not None:
                await websocket.send_text(f"Query parameter q is: {q}")
            await websocket.send_text(f"Message text was: {data} for item_id: {item_id}")
    except WebSocketDisconnect as e:
        print(f"WebSocketDisconnect: {e}")


@router.websocket("/ws/{client_id}")
async def websocket_with_clientid(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    try:
        data = await websocket.receive_text()
        await manager.send_personal_message("Hello, welcome to the chat!", client_id)
        await manager.broadcast(f"Client #{client_id} joined the chat")
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote {data}", client_id)
            await manager.broadcast(f"Client #{client_id} said {data}.")
    except WebSocketDisconnect as e:
        print(f"WebSocketDisconnect: {e}")
        manager.disconnect(client_id)
        await manager.broadcast(f"Client #{client_id} left the chat")