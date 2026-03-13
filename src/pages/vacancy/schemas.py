from enum import Enum
from typing import Annotated, Awaitable, Callable, Literal

from pydantic import BaseModel, Discriminator, Field

QuestionType = Literal["text", "radio", "radio+text", "checkbox"]


class TextQuestion(BaseModel):
    type: QuestionType = "text"
    question: str


class TextAnswer(BaseModel):
    type: QuestionType = "text"
    skip: bool = Field(
        default=False,
        description="Whether to skip this question. Use only if necessary.",
    )
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
    skip: bool = Field(
        default=False,
        description="Whether to skip this question. Use only if necessary.",
    )
    answer: int = Field(
        description="The integer index of the selected option, starting from 0."
    )


class RadioWithTextQuestion(BaseModel):
    type: QuestionType = "radio+text"
    question: str
    options: list[str] = Field(default_factory=list, min_length=1)

    def format_options(self) -> str:
        """Formats options specifically for LLM prompts."""
        return "\n".join([f"[{i}] {opt}" for i, opt in enumerate(self.options)])


class RadioWithTextAnswer(BaseModel):
    type: QuestionType = "radio+text"
    skip: bool = Field(
        default=False,
        description="Whether to skip this question. Use only if necessary.",
    )
    option: int = Field(
        0, description="The integer index of the selected option, starting from 0."
    )
    answer: str | None = Field(
        None,
        description="The concise free-form text answer to the question. Optional, overrides option if provided.",
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
    skip: bool = Field(
        default=False,
        description="Whether to skip this question. Use only if necessary.",
    )
    answer: list[int] = Field(
        description="A list of integer indices for the selected options, starting from 0."
    )


VacancyQuestion = Annotated[
    CheckboxQuestion | RadioQuestion | RadioWithTextQuestion | TextQuestion,
    Discriminator("type"),
]

VacancyQuestionAnswer = Annotated[
    CheckboxAnswer | RadioAnswer | RadioWithTextAnswer | TextAnswer,
    Discriminator("type"),
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
