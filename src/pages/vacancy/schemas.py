from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

QuestionType = Literal["text", "radio", "checkbox"]


class TextQuestion(BaseModel):
    type: QuestionType = "text"
    question: str


class TextQuestionAnswer(BaseModel):
    type: QuestionType = "text"
    question: str
    answer: str


class RadioQuestion(BaseModel):
    type: QuestionType = "radio"
    question: str
    options: list[str] = Field(default_factory=list, min_length=1)


class RadioAnswer(BaseModel):
    type: QuestionType = "radio"
    question: str
    answer: int
    options: list[str] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_answer(self):
        if self.answer is not None and (
            self.answer < 0 or self.answer >= len(self.options)
        ):
            raise ValueError("Answer index out of range. Please choose a valid option.")
        return self


class CheckboxQuestion(BaseModel):
    type: QuestionType = "checkbox"
    question: str
    options: list[str] = Field(default_factory=list, min_length=1)


class CheckboxAnswer(BaseModel):
    type: QuestionType = "checkbox"
    question: str
    answer: set[int]
    options: list[str] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_answer(self):
        if self.answer is not None:
            for opt in self.answer:
                if opt < 0 or opt >= len(self.options):
                    raise ValueError(
                        f"Answer index {opt} out of range. Please choose a valid option."
                    )
        return self


class VacancyQuestion(BaseModel):
    details: CheckboxQuestion | RadioQuestion | TextQuestion = Field(
        ..., discriminator="type"
    )


class VacancyQuestionAnswer(BaseModel):
    details: CheckboxAnswer | RadioAnswer | TextQuestionAnswer = Field(
        ..., discriminator="type"
    )


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
