import logging

from fastapi import FastAPI

from whatsapp.whatsapp_response import whatsapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI()
app.include_router(whatsapp_router)