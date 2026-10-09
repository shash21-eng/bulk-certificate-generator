from pydantic import BaseModel, Field

class RecipientInput(BaseModel):
    # Per-recipient validation is intentional: malformed data must not reject a whole batch.
    name: str = ""
    email: str = ""
    course: str = ""

class CreateJobRequest(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    issuer: str = Field(default="Certificate Team", max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1, max_length=500)

class RecipientResult(BaseModel):
    id: int
    name: str | None
    email: str | None
    course: str | None
    status: str
    certificate_url: str | None = None
    error: str | None = None

class JobResult(BaseModel):
    id: str
    status: str
    total: int
    succeeded: int
    failed: int
    created_at: str
    completed_at: str | None
    recipients: list[RecipientResult]
