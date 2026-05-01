from typing import List, Optional

from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: str = Field(..., example="Licenciado en Ingeniería Informática")
    institution: str = Field(..., example="Universidad Nacional")
    start_date: str = Field(..., example="2020-03")
    end_date: str = Field(..., example="2024-12")
    location: Optional[str] = Field(None, example="Buenos Aires, Argentina")
    description: Optional[str] = Field(None, example="Especialización en inteligencia artificial.")


class ExperienceItem(BaseModel):
    job_title: str = Field(..., example="Desarrollador Backend")
    company: str = Field(..., example="TechLabs S.A.")
    start_date: str = Field(..., example="2022-05")
    end_date: str = Field(..., example="2024-04")
    location: Optional[str] = Field(None, example="Remoto")
    responsibilities: Optional[List[str]] = Field(
        None,
        example=[
            "Desarrollo de APIs REST con Python",
            "Implementación de sistemas de autenticación"
        ]
    )
    achievements: Optional[List[str]] = Field(
        None,
        example=["Reduje tiempos de respuesta en un 40%."]
    )


class LanguageSkill(BaseModel):
    language: str = Field(..., example="Español")
    level: str = Field(..., example="Nativo")


class CertificationItem(BaseModel):
    title: str = Field(..., example="Certificación AWS Solutions Architect")
    issuer: Optional[str] = Field(None, example="Amazon Web Services")
    date: Optional[str] = Field(None, example="2024-01")
    description: Optional[str] = Field(None, example="Formación en arquitecturas cloud.")


class CVRequest(BaseModel):
    full_name: str = Field(..., example="María Pérez")
    email: str = Field(..., example="maria.perez@example.com")
    phone: Optional[str] = Field(None, example="+54 9 11 1234 5678")
    location: Optional[str] = Field(None, example="Buenos Aires, Argentina")
    linkedin: Optional[str] = Field(None, example="https://www.linkedin.com/in/mariaperez")
    github: Optional[str] = Field(None, example="https://github.com/mariaperez")
    professional_title: Optional[str] = Field(None, example="Ingeniera de Software")
    summary: Optional[str] = Field(None, example="Profesional con experiencia en desarrollo de software y proyectos de inteligencia artificial.")
    career_objective: Optional[str] = Field(None, example="Busco un puesto de liderazgo técnico en desarrollo backend.")
    education: Optional[List[EducationItem]] = Field(None)
    experience: Optional[List[ExperienceItem]] = Field(None)
    technical_skills: Optional[List[str]] = Field(None, example=["Python", "FastAPI", "Docker"])
    soft_skills: Optional[List[str]] = Field(None, example=["Comunicación", "Trabajo en equipo"])
    languages: Optional[List[LanguageSkill]] = Field(None)
    certifications: Optional[List[CertificationItem]] = Field(None)
    additional_information: Optional[str] = Field(None, example="Disponibilidad inmediata para trabajar de forma remota.")
