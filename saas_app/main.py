from fastapi import FastAPI
import uvicorn

from saas_app.router import websocket

app = FastAPI()


app.include_router(websocket.router)

