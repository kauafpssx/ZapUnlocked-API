from pydantic import BaseModel

class WebhookConfigIn(BaseModel):
    url: str
    method: str = "POST"
    headers: dict = {}
    body: dict = {}

class WebhookToggleIn(BaseModel):
    status: str

# These will be mapped to manageWebhook.py
