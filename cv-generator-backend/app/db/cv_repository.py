"""
Repositorio para operaciones CRUD de CVs en MongoDB
"""
import logging
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.db.session import get_db
from app.db.models import CVDocument
from app.schemas.cv_response import CVResponse

logger = logging.getLogger(__name__)


class CVRepository:
    """
    Clase para manejar todas las operaciones de base de datos relacionadas con CVs
    """
    
    COLLECTION_NAME = "cvs"

    @staticmethod
    async def save_cv(cv_data: CVResponse, user_id: str) -> str:
        """
        Guarda un CV generado en MongoDB
        
        Args:
            cv_data: Objeto CVResponse con los datos del CV
            user_id: ID del usuario propietario del CV
            
        Returns:
            ID del documento guardado (ObjectId como string)
        """
        try:
            db = get_db()
            collection = db[CVRepository.COLLECTION_NAME]
            
            # Construir documento para MongoDB
            cv_document = {
                "user_id": user_id,
                "personal": cv_data.personal.model_dump(),
                "perfil": cv_data.perfil.model_dump(),
                "experiencias": [exp.model_dump() for exp in cv_data.experiencias],
                "formacion": [form.model_dump() for form in cv_data.formacion],
                "habilidades": cv_data.habilidades,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            result = await collection.insert_one(cv_document)
            logger.info(f"CV guardado exitosamente. ID: {result.inserted_id}, user_id: {user_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error al guardar CV en MongoDB: {e}")
            raise

    @staticmethod
    async def get_cv_by_id(cv_id: str) -> Optional[dict]:
        """
        Obtiene un CV por su ID
        
        Args:
            cv_id: ID del documento CV (ObjectId como string)
            
        Returns:
            Documento CV o None si no existe
        """
        try:
            db = get_db()
            collection = db[CVRepository.COLLECTION_NAME]
            
            cv = await collection.find_one({"_id": ObjectId(cv_id)})
            
            if cv:
                cv["_id"] = str(cv["_id"])
            
            return cv
            
        except Exception as e:
            logger.error(f"Error al obtener CV {cv_id}: {e}")
            raise

    @staticmethod
    async def get_cvs_by_user(user_id: str) -> List[dict]:
        """
        Obtiene todos los CVs de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de documentos CV
        """
        try:
            db = get_db()
            collection = db[CVRepository.COLLECTION_NAME]
            
            cvs = await collection.find({"user_id": user_id}).to_list(length=None)
            
            # Convertir ObjectId a string
            for cv in cvs:
                cv["_id"] = str(cv["_id"])
            
            logger.info(f"Se obtuvieron {len(cvs)} CVs para usuario {user_id}")
            return cvs
            
        except Exception as e:
            logger.error(f"Error al obtener CVs del usuario {user_id}: {e}")
            raise

    @staticmethod
    async def update_cv(cv_id: str, cv_data: CVResponse) -> bool:
        """
        Actualiza un CV existente
        
        Args:
            cv_id: ID del documento CV
            cv_data: Nuevos datos del CV
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            db = get_db()
            collection = db[CVRepository.COLLECTION_NAME]
            
            update_data = {
                "personal": cv_data.personal.model_dump(),
                "perfil": cv_data.perfil.model_dump(),
                "experiencias": [exp.model_dump() for exp in cv_data.experiencias],
                "formacion": [form.model_dump() for form in cv_data.formacion],
                "habilidades": cv_data.habilidades,
                "updated_at": datetime.utcnow(),
            }
            
            result = await collection.update_one(
                {"_id": ObjectId(cv_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"CV {cv_id} actualizado exitosamente")
                return True
            else:
                logger.warning(f"No se encontró CV con ID {cv_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error al actualizar CV {cv_id}: {e}")
            raise

    @staticmethod
    async def delete_cv(cv_id: str) -> bool:
        """
        Elimina un CV
        
        Args:
            cv_id: ID del documento CV
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            db = get_db()
            collection = db[CVRepository.COLLECTION_NAME]
            
            result = await collection.delete_one({"_id": ObjectId(cv_id)})
            
            if result.deleted_count > 0:
                logger.info(f"CV {cv_id} eliminado exitosamente")
                return True
            else:
                logger.warning(f"No se encontró CV con ID {cv_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error al eliminar CV {cv_id}: {e}")
            raise
