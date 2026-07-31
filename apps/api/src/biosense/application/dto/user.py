from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: str
    auth_user_id: str
    email: EmailStr
    org_name: str | None = None
    role: str = Field(default="researcher")
    created_at: str
