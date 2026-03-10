from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class VacancyQuestion(BaseModel):
    question: str
    type: Literal["text", "radio", "multiple"]
    options: list[str] = Field(default_factory=list)


class VacancyStatus(Enum):
    NEW = "new"
    AWAITING = "awaiting"
    INTERVIEW = "interview"
    REJECTED = "rejected"


class Vacancy(BaseModel):
    title: str = Field(..., description="Название вакансии")
    description: str = Field(..., description="Описание вакансии")
    salary: str | None = Field(None, description="Зарплата")
    work_format: str | None = Field(None, description="Формат работы")
    experience: str | None = Field(None, description="Опыт работы")
    work_schedule: str | None = Field(None, description="График работы")
    hiring_formats: str | None = Field(None, description="Оформление")
    employment_form: str | None = Field(None, description="Форма занятости")
    working_hours: str | None = Field(None, description="Рабочие часы")

    is_applied_to: bool
    status: VacancyStatus
