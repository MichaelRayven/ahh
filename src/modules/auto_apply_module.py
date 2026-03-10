import asyncio
import logging

from playwright.async_api import Page, TimeoutError

from src.config.settings import get_app_settings
from src.modules.base import Module

settings = get_app_settings()
logger = logging.getLogger(__name__)


class AutoApplyModule(Module):
    def __init__(self, context):
        super().__init__(context)

    async def run(self):
        page = await self._context.new_page()

        # Search
        search_url = settings.search_query.search_url
        await page.goto(search_url)

        vacancies = await page.query_selector_all('[data-qa="serp-item__title"]')

        chunks: list[list[str]] = [[] for _ in range(settings.concurrency)]
        for i, link in enumerate(vacancies):
            link = await link.get_attribute("href")
            if link:
                chunks[i % settings.concurrency].append(link)

        pages = [await self._context.new_page() for _ in range(settings.concurrency)]

        async def _process_chunk(page: Page, chunk: list[str]):
            try:
                for link in chunk:
                    vacancy_chat_locator = page.locator(
                        '[data-qa="vacancy-response-link-view-topic"]'
                    )
                    # vacancy_salary_locator = page.locator('[data-qa="vacancy-salary"]')
                    # vacancy_experience_locator = page.locator(
                    #     '[data-qa="vacancy-experience"]'
                    # )
                    # vacancy_employment_form_locator = page.locator(
                    #     '[data-qa="common-employment-text"]'
                    # )
                    # vacancy_work_format_locator = page.locator(
                    #     '[data-qa="work-formats-text"]'
                    # )
                    # vacancy_title_locator = page.locator('[data-qa="vacancy-title"]')
                    # vacancy_description_locator = page.locator(
                    #     '[data-qa="vacancy-description"]'
                    # )
                    apply_button_locator = page.locator(
                        '[data-qa="vacancy-response-link-top"]'
                    )

                    await page.goto(link)

                    # vacancy_description = (
                    #     await vacancy_description_locator.text_content()
                    #     if await vacancy_description_locator.is_visible()
                    #     else None
                    # )
                    # vacancy_title = (
                    #     await vacancy_title_locator.text_content()
                    #     if await vacancy_title_locator.is_visible()
                    #     else None
                    # )
                    # vacancy_salary = (
                    #     await vacancy_salary_locator.text_content()
                    #     if await vacancy_salary_locator.is_visible()
                    #     else None
                    # )
                    # vacancy_experience = (
                    #     await vacancy_experience_locator.text_content()
                    #     if await vacancy_experience_locator.is_visible()
                    #     else None
                    # )
                    # vacancy_employment_form = (
                    #     await vacancy_employment_form_locator.text_content()
                    #     if await vacancy_employment_form_locator.is_visible()
                    #     else None
                    # )
                    # vacancy_work_format = (
                    #     await vacancy_work_format_locator.text_content()
                    #     if await vacancy_work_format_locator.is_visible()
                    #     else None
                    # )

                    # print(
                    #     vacancy_description,
                    #     vacancy_title,
                    #     vacancy_salary,
                    #     vacancy_experience,
                    #     vacancy_employment_form,
                    #     vacancy_work_format,
                    # )

                    # Check for vacancies we've already applied to
                    if not await vacancy_chat_locator.is_visible():
                        await apply_button_locator.first.click()
                        await page.wait_for_load_state("networkidle")
            except TimeoutError:
                logger.error("Failed to apply: %s", link)

        tasks = [
            _process_chunk(pages[i], chunks[i]) for i in range(settings.concurrency)
        ]

        await asyncio.gather(*tasks)
