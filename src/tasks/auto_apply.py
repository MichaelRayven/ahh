import asyncio
import logging
import re

from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from playwright.async_api import Page
from src.config.settings import get_app_settings
from src.pages.search.page import SearchPage
from src.pages.vacancy.page import VacancyPage
from src.pages.vacancy.schemas import (
    CheckboxAnswer,
    CheckboxQuestion,
    RadioAnswer,
    RadioQuestion,
    RadioWithTextAnswer,
    RadioWithTextQuestion,
    TextAnswer,
    TextQuestion,
    Vacancy,
    VacancyQuestion,
    VacancyQuestionAnswer,
)
from src.tasks.base import BaseTask

settings = get_app_settings()
logger = logging.getLogger(__name__)


class AutoApplyTask(BaseTask):
    def __init__(self, context):
        super().__init__(context)
        self.llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.05,
        )

    async def generate_cover_letter(self, vacancy: Vacancy) -> str:
        prompt = PromptTemplate.from_template(settings.prompts.cover_letter)
        chain = prompt | self.llm
        result = await chain.ainvoke(
            {
                "title": vacancy.title,
                "description": vacancy.description,
                "default_cover_letter": settings.default_cover_letter,
            }
        )
        return str(getattr(result, "content", ""))

    async def generate_answers(
        self, vacancy: Vacancy, questions: list[VacancyQuestion]
    ) -> list[VacancyQuestionAnswer]:
        answers = []
        for q in questions:
            match q:
                case TextQuestion(question=question):
                    prompt = PromptTemplate.from_template(settings.prompts.text_answer)
                    chain = prompt | self.llm.with_structured_output(TextAnswer)
                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "default_answers": settings.default_answers,
                        }
                    )
                    answers.append(result)
                case RadioQuestion(question=question):
                    prompt = PromptTemplate.from_template(settings.prompts.radio_answer)
                    chain = prompt | self.llm.with_structured_output(RadioAnswer)
                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": settings.default_answers,
                        }
                    )
                    answers.append(result)
                case CheckboxQuestion(question=question):
                    prompt = PromptTemplate.from_template(
                        settings.prompts.checkbox_answer
                    )
                    chain = prompt | self.llm.with_structured_output(CheckboxAnswer)
                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": settings.default_answers,
                        }
                    )
                    answers.append(result)
                case RadioWithTextQuestion(question=question):
                    prompt = PromptTemplate.from_template(settings.prompts.radio_answer)
                    chain = prompt | self.llm.with_structured_output(
                        RadioWithTextAnswer
                    )
                    result = await chain.ainvoke(
                        {
                            "title": vacancy.title,
                            "question": question,
                            "options": q.format_options(),
                            "default_answers": settings.default_answers,
                        }
                    )
                    answers.append(result)
                case _:
                    raise ValueError(f"Unsupported question type: {question}")

        return answers

    async def run(self):
        page = await self._context.new_page()

        search_page = SearchPage(page, settings.search_query)
        await search_page.navigate()

        vacancies = await search_page.get_vacancies_page(0)

        chunks: list[list[str]] = [[] for _ in range(settings.concurrency)]
        for i, link_element in enumerate(vacancies):
            link = await link_element.get_attribute("href")
            if link:
                chunks[i % settings.concurrency].append(link)

        pages = [await self._context.new_page() for _ in range(settings.concurrency)]

        async def _process_chunk(page: Page, chunk: list[str]):
            for link in chunk:
                match = re.search(r"/vacancy/(\d+)", link)
                if not match:
                    continue
                vacancy_id = match.group(1)

                vacancy_page = VacancyPage(
                    page=page,
                    id=vacancy_id,
                )
                vacancy_page.set_cover_letter_generator(self.generate_cover_letter)
                vacancy_page.set_answers_generator(self.generate_answers)

                try:
                    await vacancy_page.navigate()
                    await vacancy_page.apply()
                except Exception as e:
                    logger.error("Failed to apply to vacancy %s: %s", vacancy_id, e)

        tasks = [
            _process_chunk(pages[i], chunks[i]) for i in range(settings.concurrency)
        ]

        await asyncio.gather(*tasks)
