from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Identity", version="0.1.0")


class DemoLogin(BaseModel):
    email: str = Field(min_length=3)


@app.get("/health")
def health():
    return {"status": "ok", "service": "identity"}


@app.post("/identity/demo-login")
def demo_login(body: DemoLogin):
    return {
        "user_id": "demo-user",
        "email": body.email,
        "display_name": body.email.split("@")[0].title(),
        "roles": ["user"],
        "org_id": "demo-org",
    }
