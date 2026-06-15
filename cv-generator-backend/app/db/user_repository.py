from typing import Optional
from app.db.models import UserDocument
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

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
    
    async def get_all_users(self) -> list[UserDocument]:
        """Recupera todos los usuarios registrados en la base de datos"""
        users = []
        # Buscamos todos los documentos sin filtros ({})
        async for user_dict in self.collection.find({}):
            user_dict["_id"] = str(user_dict["_id"])
            users.append(UserDocument(**user_dict))
        return users