from typing import Callable
from urllib.parse import urlsplit

from playwright.async_api import Page

from src.pages.base import BasePage

from .schemas import (
    RadioAnswer,
    RadioQuestion,
    TextQuestion,
    TextQuestionAnswer,
    Vacancy,
    VacancyQuestion,
    VacancyQuestionAnswer,
    VacancyStatus,
)


class VacancyQuestionsPage(BasePage):
    """Special class for vacancy quiestions page which can only be accessed after clicking apply to vacancy."""

    URL = "https://hh.ru/applicant/vacancy_response"

    def __init__(self, page: Page, id: str):
        self._page = page
        self.id = id

        # Locators
        self.description = page.locator('[data-qa="test-description"]')
        self.submit_button = page.locator('[data-qa="vacancy-response-submit-popup"]')
        self.skip_button = page.locator(
            '[data-qa="vacancy-response-link-no-questions"]'
        )
        self.tasks = page.locator('[data-qa="task-body"]')

    async def navigate(self):
        await self._page.goto(self.URL + "?vacancyId=" + self.id)

    async def get_questions(self) -> list[VacancyQuestion]:
        questions: list[VacancyQuestion] = []
        for task in await self.tasks.all():
            question = await task.locator('[data-qa="task-question"]').text_content()

            text_input = task.locator('[data-qa="textarea-native-wrapper"] textarea')
            radio_options = task.locator('label[data-qa="cell"]')

            # Single option question
            if await radio_options.count() > 0:
                options = [
                    await option.text_content() or ""
                    for option in await radio_options.all()
                ]
                questions.append(
                    VacancyQuestion(
                        details=RadioQuestion(question=question or "", options=options),
                    )
                )
            # Text question
            elif await text_input.is_visible():
                questions.append(
                    VacancyQuestion(
                        details=TextQuestion(
                            question=question or "",
                        ),
                    )
                )
            else:
                raise ValueError(
                    f"Unknown question type for task: {question}, on page: {self.URL + '?vacancyId=' + self.id}"
                )

        return questions

    async def answer_questions(self, answers: list[VacancyQuestionAnswer]) -> None:
        for idx, answer in enumerate(answers):
            task = self.tasks.nth(idx)
            if isinstance(answer.details, RadioAnswer):
                option = task.locator('label[data-qa="cell"]').nth(
                    answer.details.answer
                )
                await option.click()
            elif isinstance(answer.details, TextQuestionAnswer):
                text_input = task.locator(
                    '[data-qa="textarea-native-wrapper"] textarea'
                )
                await text_input.clear()
                await text_input.fill(answer.details.answer)
            else:
                raise ValueError(f"Unknown question type: {answer}")


class VacancyPage(BasePage):
    URL = "https://hh.ru/vacancy"

    def __init__(
        self, page: Page, id: str, get_cover_letter: Callable[[str], str] | None = None
    ):
        super().__init__(page)
        self.id = id
        self.get_cover_letter = get_cover_letter

        # Locators
        self.vacancy_salary = page.locator('[data-qa="vacancy-salary"]')
        self.vacancy_experience = page.locator('[data-qa="vacancy-experience"]')
        self.vacancy_employment_form = page.locator(
            '[data-qa="common-employment-text"]'
        )
        self.vacancy_work_format = page.locator('[data-qa="work-formats-text"]')
        self.vacancy_hiring_formats = page.locator('[data-qa="vacancy-hiring-formats"]')
        self.vacancy_working_hours = page.locator('[data-qa="working-hours-text"]')
        self.vacancy_work_schedule = page.locator(
            '[data-qa="work-schedule-by-days-text"]'
        )
        self.vacancy_work_hours = page.locator('[data-qa="working-hours-text"]')
        self.vacancy_title = page.locator('[data-qa="vacancy-title"]')
        self.vacancy_description = page.locator('[data-qa="vacancy-description"]')
        self.vacancy_status_card = page.locator('[class^="card-content"]').first

        self.vacancy_chat = page.locator(
            '[data-qa="vacancy-response-link-view-topic"]'
        ).first
        self.apply_button = page.locator('[data-qa="vacancy-response-link-top"]').first

        # Optional cover letter submission
        self.cover_letter_textarea = page.locator(
            '[data-qa="textarea-native-wrapper"] textarea'
        )
        self.cover_letter_submit_button = page.locator(
            '[data-qa="vacancy-response-letter-submit"]'
        )

        # Popup requiring cover letter
        self.popup_cover_letter_textarea = page.locator(
            '[data-qa="vacancy-response-popup-form-letter-input"]'
        )
        self.popup_cover_letter_submit_button = page.locator(
            '[data-qa="vacancy-response-submit-popup"]'
        )

    async def navigate(self) -> None:
        await self._page.goto(self.URL + "/" + self.id)

    async def get_vacancy_info(self) -> Vacancy:
        salary = (
            await self.vacancy_salary.text_content()
            if await self.vacancy_salary.is_visible()
            else ""
        )
        experience = (
            await self.vacancy_experience.text_content()
            if await self.vacancy_experience.is_visible()
            else ""
        )
        employment_form = (
            await self.vacancy_employment_form.text_content()
            if await self.vacancy_employment_form.is_visible()
            else ""
        )
        work_format = (
            await self.vacancy_work_format.text_content()
            if await self.vacancy_work_format.is_visible()
            else ""
        )
        hiring_formats = (
            await self.vacancy_hiring_formats.text_content()
            if await self.vacancy_hiring_formats.is_visible()
            else ""
        )
        work_schedule = (
            await self.vacancy_work_schedule.text_content() or ""
            if await self.vacancy_work_schedule.is_visible()
            else None
        )
        working_hours = (
            await self.vacancy_working_hours.text_content() or ""
            if await self.vacancy_working_hours.is_visible()
            else None
        )

        if await self.vacancy_status_card.is_visible():
            status_string = await self.vacancy_status_card.text_content()
            if status_string == "Ваc пригласили":
                status = VacancyStatus.INTERVIEW
            elif status_string == "Вам отказали":
                status = VacancyStatus.REJECTED
            elif status_string == "Вы откликнулись":
                status = VacancyStatus.AWAITING
        else:
            status = VacancyStatus.NEW

        if status != VacancyStatus.NEW or await self.vacancy_chat.is_visible():
            is_applied_to = True
        else:
            is_applied_to = False

        return Vacancy(
            title=await self.vacancy_title.text_content() or "",
            description=await self.vacancy_description.text_content() or "",
            work_format=work_format,
            experience=experience,
            salary=salary,
            work_schedule=work_schedule,
            hiring_formats=hiring_formats,
            employment_form=employment_form,
            working_hours=working_hours,
            status=status,
            is_applied_to=is_applied_to,
        )

    async def apply(self):
        """Apply to the vacancy if not already applied."""
        # Vacancy is already applied to.
        vacancy = await self.get_vacancy_info()
        cover_letter = ""

        if vacancy.is_applied_to:
            return

        # Apply to the vacancy
        await self.apply_button.click()
        await self._page.wait_for_load_state("networkidle")

        # Fill required cover letter
        if await self.popup_cover_letter_textarea.is_visible():
            await self.popup_cover_letter_textarea.fill(cover_letter)
            await self.popup_cover_letter_submit_button.click()
            await self._page.wait_for_load_state("networkidle")

        # Fill optional cover letter
        if await self.cover_letter_textarea.is_visible():
            await self.cover_letter_textarea.fill(cover_letter)
            await self.cover_letter_submit_button.click()
            await self._page.wait_for_load_state("networkidle")

        # Redirected to questions page
        if urlsplit(self._page.url).path != f"/vacancy/{self.id}":
            # questions_page = VacancyQuestionsPage(self._page, self.id)
            # TODO: Answer questions and submit
            await self._page.wait_for_load_state("networkidle")
