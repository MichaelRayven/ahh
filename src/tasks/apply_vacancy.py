import logging
from urllib.parse import urlsplit

from playwright.async_api import BrowserContext, Page
from src.config.settings import Settings
from src.vacancy.pages import VacancyPage, VacancyQuestionsPage
from src.vacancy.schemas import Vacancy, VacancyApplicationResponse
from src.generation.services import LLMService
from src.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class ApplyVacancyTask(BaseTask):
    def __init__(
        self,
        context: BrowserContext,
        settings: Settings,
        llm_service: LLMService,
        vacancy_id: str,
        resume_id: str | None,
        page: Page,
    ):
        super().__init__(context)
        self._settings = settings
        self._llm_service = llm_service
        self._vacancy_id = vacancy_id
        self._resume_id = resume_id
        self._page = page

    async def _handle_relocation_warning(self, vacancy_page: VacancyPage):
        """Handle relocation warning."""
        if not self._settings.apply_with_relocation:
            return

        title = vacancy_page._page.locator('[data-qa="relocation-warning-title"]')
        confirm_relocation_button = vacancy_page._page.locator(
            '[data-qa="relocation-warning-confirm"]'
        )
        abort_relocation_button = vacancy_page._page.locator(
            '[data-qa="relocation-warning-abort"]'
        )

        if await title.is_visible():
            if self._settings.apply_with_relocation:
                await confirm_relocation_button.click()
            else:
                await abort_relocation_button.click()
            await vacancy_page._page.wait_for_timeout(2000)

    async def _handle_required_cover_letter(
        self, vacancy_page: VacancyPage, cover_letter: str
    ):
        """Handle required cover letter."""
        if not self._settings.apply_with_cover_letter:
            return

        cover_letter_textarea = vacancy_page._page.locator(
            '[data-qa="vacancy-response-popup-form-letter-input"]'
        )
        cover_letter_submit_button = vacancy_page._page.locator(
            '[data-qa="vacancy-response-submit-popup"]'
        )

        if await cover_letter_textarea.is_visible():
            await cover_letter_textarea.fill(cover_letter)
            await cover_letter_submit_button.click()
            await vacancy_page._page.wait_for_timeout(2000)

    async def _handle_questions_page(
        self, vacancy_page: VacancyPage, cover_letter: str, vacancy: Vacancy
    ):
        """Handle questions page."""
        if not self._settings.apply_with_questions:
            return

        if urlsplit(vacancy_page._page.url).path != f"/vacancy/{self._vacancy_id}":
            questions_page = VacancyQuestionsPage(vacancy_page._page, self._vacancy_id)
            if self._settings.generate_questions:
                questions = await questions_page.get_questions()
                answers = await self._llm_service.generate_answers(
                    vacancy, questions, self._resume_id
                )
                await questions_page.answer_questions(answers)

            if self._settings.apply_with_cover_letter:
                await questions_page.attach_cover_letter(cover_letter)

            await questions_page.apply()
            await vacancy_page._page.wait_for_timeout(2000)

    async def _handle_optional_cover_letter(
        self, vacancy_page: VacancyPage, cover_letter: str
    ):
        """Handle optional cover letter."""

        if not self._settings.apply_with_cover_letter:
            return

        cover_letter_wrapper = vacancy_page._page.locator(
            '[data-qa="vacancy-response-letter-informer"]'
        )

        cover_letter_textarea = cover_letter_wrapper.locator("textarea")
        cover_letter_submit_button = cover_letter_wrapper.locator(
            '[data-qa="vacancy-response-letter-submit"]'
        )

        if await cover_letter_textarea.is_visible():
            await cover_letter_textarea.fill(cover_letter)
            await cover_letter_submit_button.click()
            await vacancy_page._page.wait_for_timeout(2000)

    async def _handle_salary_popup(self, vacancy_page: VacancyPage):
        close_button = vacancy_page._page.locator(
            '[data-qa="additional-data-collector__popup-close"]'
        )
        if await close_button.is_visible():
            await close_button.click()
            await vacancy_page._page.wait_for_timeout(2000)

    async def run(self):
        vacancy_page = VacancyPage(self._page, self._vacancy_id)

        try:
            await vacancy_page.navigate()
            vacancy = await vacancy_page.get_vacancy_info()

            # Vacancy is already applied to.
            if vacancy.is_applied_to:
                return

            cover_letter: str = ""
            if self._settings.apply_with_cover_letter:
                cover_letter = self._settings.default_cover_letter or ""

                if self._settings.generate_cover_letter:
                    cover_letter = await self._llm_service.generate_cover_letter(
                        vacancy, self._resume_id
                    )

            async with vacancy_page._page.expect_response(
                lambda r: (
                    "/applicant/vacancy_response" in r.url and r.request.method == "GET"
                )
            ) as response_info:
                await vacancy_page.apply_button.click()

            response = await response_info.value
            response_json = await response.json()
            vacancy_response = VacancyApplicationResponse(**response_json)

            logger.debug(f"Parsed VacancyApplicationResponse: {vacancy_response}")

            if vacancy_response.response_impossible:
                logger.warning(
                    "Application impossible for vacancy %s", self._vacancy_id
                )
                return
            if vacancy_response.already_applied:
                logger.info("Already applied to vacancy %s", self._vacancy_id)
                return

            # 1. Relocation warning shown
            if (
                vacancy_response.relocation_warning
                and vacancy_response.relocation_warning.show
            ):
                await self._handle_relocation_warning(vacancy_page)
            # 2. Popup requiring cover letter shown
            if vacancy_response.letter_required:
                await self._handle_required_cover_letter(vacancy_page, cover_letter)
            # 3. Redirected to questions page
            if vacancy_response.type == "test-required":
                await self._handle_questions_page(vacancy_page, cover_letter, vacancy)

            await self._handle_optional_cover_letter(vacancy_page, cover_letter)
        except Exception as e:
            logger.error("Failed to apply to vacancy %s: %s", self._vacancy_id, e)
