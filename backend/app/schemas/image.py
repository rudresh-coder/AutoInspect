from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageUploadResponse(BaseModel):
    processing_id: str
    status: str
    filename: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)