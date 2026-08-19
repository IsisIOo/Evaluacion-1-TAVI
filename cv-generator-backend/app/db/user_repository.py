from typing import Optional
from app.db.models import UserDocument
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def get_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Recupera un usuario por su id de MongoDB, o None si no existe o el id es inválido."""
        try:
            user_dict = await self.collection.find_one({"_id": ObjectId(user_id)})
        except InvalidId:
            return None
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserDocument(**user_dict)
        return None

    async def get_by_email(self, email: str) -> Optional[UserDocument]:
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            # Forzamos que el _id sea un string antes de pasárselo a Pydantic
            user_dict["_id"] = str(user_dict["_id"])
            return UserDocument(**user_dict)
        return None

    async def create_user(self, user_doc: UserDocument) -> UserDocument:
        user_dict = user_doc.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(user_dict)
        user_doc.id = str(result.inserted_id)
        return user_doc