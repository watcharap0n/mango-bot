from datetime import datetime
from db import PyObjectId
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field


class Area(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class Areas(BaseModel):
    type: Optional[str] = None
    area: Optional[Area] = None
    text: Optional[str] = None
    linkUri: Optional[str] = None


class Size(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None


class ImageMap(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    access_token: str
    type_url: Optional[str] = 'URL'
    local_file: Optional[str] = None
    base_url_image: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "hello mapping",
                "base_url_image": "https://github.com",
                "access_token": "token long live",
                "content": "",
                "description": "description mapping",
            }
        }


class Mapping(ImageMap):
    size: Optional[Size] = None
    areas: Optional[List[Areas]] = None

    class Config:
        schema_extra = {
            "size": {
                "width": 480,
                "height": 480
            },
            "areas": [
                {
                    "bounds": {"x": 898, "y": 330, "width": 550, "height": 414},
                    "action": {"type": "message", "data": "action"}
                },
                {
                    "bounds": {"x": 898, "y": 330, "width": 550, "height": 414},
                    "action": {"type": "message", "data": "action1"}
                }
            ],
        }


class TokenUser(Mapping):
    uid: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[datetime] = None

    class Config:
        schema_extra = {
            "uid": "generate token uid",
            "date": "12/01/2022",
            "time": "12:00:00",
        }


class UpdateImageMap(BaseModel):
    name: str
    access_token: str
    base_url_image: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    size: Optional[Size] = None
    areas: Optional[List[Areas]] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "update hello mapping",
                "access_token": "update token long live",
                "base_url_image": "https://github.com",
                "content": "",
                "description": "update description mapping",
                "size": {
                    "width": 480,
                    "height": 480
                },
                "areas": [
                    {
                        "bounds": {"x": 123, "y": 330, "width": 550, "height": 414},
                        "action": {"type": "message", "data": "action"}
                    },
                    {
                        "bounds": {"x": 898, "y": 330, "width": 550, "height": 414},
                        "action": {"type": "message", "data": "action1"}
                    }
                ],
            }
        }
