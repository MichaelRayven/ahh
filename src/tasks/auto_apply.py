import asyncio
import logging
import re

from playwright.async_api import Page
from src.config.settings import get_app_settings
from src.search.pages import SearchPage
from src.tasks.apply_vacancy import ApplyVacancyTask
from src.generation.services import LLMService
from src.tasks.base import BaseTask

settings = get_app_settings()
logger = logging.getLogger(__name__)


class AutoApplyTask(BaseTask):
    def __init__(self, context):
        super().__init__(context)
        self.llm_service = LLMService(settings)

    async def run(self):
        resume_id = None
        if settings.default_resume_path:
            logger.info(f"Indexing default resume from {settings.default_resume_path}")
            resume_id = self.llm_service.index_resume(settings.default_resume_path)

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

                apply_task = ApplyVacancyTask(
                    context=self._context,
                    settings=settings,
                    llm_service=self.llm_service,
                    vacancy_id=vacancy_id,
                    resume_id=resume_id,
                    page=page,
                )

                try:
                    await apply_task.run()
                except Exception as e:
                    logger.error(
                        "Failed to run apply task for vacancy %s: %s", vacancy_id, e
                    )

        tasks = [
            _process_chunk(pages[i], chunks[i]) for i in range(settings.concurrency)
        ]

        await asyncio.gather(*tasks)
