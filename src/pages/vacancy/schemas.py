from enum import Enum
from typing import Awaitable, Callable, Literal, Annotated

from pydantic import BaseModel, Field, Discriminator

QuestionType = Literal["text", "radio", "checkbox"]


class TextQuestion(BaseModel):
    type: QuestionType = "text"
    question: str


class TextAnswer(BaseModel):
    type: QuestionType = "text"
    answer: str = Field(description="The concise text answer to the question.")


class RadioQuestion(BaseModel):
    type: QuestionType = "radio"
    question: str
    options: list[str] = Field(default_factory=list, min_length=1)

    def format_options(self) -> str:
        """Formats options specifically for LLM prompts."""
        return "\n".join([f"[{i}] {opt}" for i, opt in enumerate(self.options)])


class RadioAnswer(BaseModel):
    type: QuestionType = "radio"
    answer: int = Field(
        description="The integer index of the selected option, starting from 0."
    )


class CheckboxQuestion(BaseModel):
    type: QuestionType = "checkbox"
    question: str
    options: list[str] = Field(default_factory=list, min_length=1)

    def format_options(self) -> str:
        """Formats options specifically for LLM prompts."""
        return "\n".join([f"[{i}] {opt}" for i, opt in enumerate(self.options)])


class CheckboxAnswer(BaseModel):
    type: QuestionType = "checkbox"
    answer: list[int] = Field(
        description="A list of integer indices for the selected options, starting from 0."
    )


VacancyQuestion = Annotated[
    CheckboxQuestion | RadioQuestion | TextQuestion, Discriminator("type")
]

VacancyQuestionAnswer = Annotated[
    CheckboxAnswer | RadioAnswer | TextAnswer, Discriminator("type")
]


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


CoverLetterGenerator = Callable[[Vacancy], Awaitable[str]]
AnswersGenerator = Callable[
    [Vacancy, list[VacancyQuestion]], Awaitable[list[VacancyQuestionAnswer]]
]
