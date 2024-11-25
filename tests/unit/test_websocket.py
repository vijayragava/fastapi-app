import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from saas_app.main import app  # Replace with the actual import path for your FastAPI app

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_html():
    response = client.get("/websocket/")
    assert response.status_code == 200
    assert "<title>Chat</title>" in response.text

@pytest.mark.asyncio
async def test_websocket_endpoint():
    async with client.websocket_connect("/websocket/test/ws") as websocket:
        await websocket.send_text("Hello WebSocket")
        response_1 = await websocket.receive_text()
        response_2 = await websocket.receive_text()
        assert "Session cookie or token value:" in response_1
        assert "Message text was: Hello WebSocket for item_id: test" in response_2

@pytest.mark.asyncio
async def test_websocket_with_clientid():
    client_id = "123456"
    async with client.websocket_connect(f"/websocket/ws/{client_id}") as websocket:
        await websocket.send_text("Hi")
        message = await websocket.receive_text()
        assert "Hello, welcome to the chat!" in message
        broadcast_message = await websocket.receive_text()
        assert f"Client #{client_id} joined the chat" in broadcast_message

        # Test sending a message
        await websocket.send_text("Hello Everyone")
        personal_message = await websocket.receive_text()
        broadcast_message = await websocket.receive_text()
        assert f"You wrote Hello Everyone" in personal_message
        assert f"Client #{client_id} said Hello Everyone." in broadcast_message

        # Test disconnection
        await websocket.close()
        with pytest.raises(WebSocketDisconnect):
            await websocket.receive_text()