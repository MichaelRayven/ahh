from urllib.parse import urlsplit

from playwright.async_api import Locator, Page
from src.config.settings import get_app_settings
from src.pages.base import BasePage
from src.pages.vacancy.exceptions import VacancyApplicationError

from .schemas import (
    AnswersGenerator,
    CheckboxAnswer,
    CheckboxQuestion,
    CoverLetterGenerator,
    QuestionType,
    RadioAnswer,
    RadioQuestion,
    RadioWithTextAnswer,
    RadioWithTextQuestion,
    TextAnswer,
    TextQuestion,
    Vacancy,
    VacancyQuestion,
    VacancyQuestionAnswer,
    VacancyStatus,
)

settings = get_app_settings()


class VacancyQuestionsPage(BasePage):
    """Special class for vacancy quiestions page which can only be accessed after clicking apply to vacancy."""

    URL = "https://hh.ru/applicant/vacancy_response"

    def __init__(self, page: Page, id: str):
        self._page = page
        self.id = id

        # Locators
        self.description = page.locator('[data-qa="test-description"]')
        self.tasks = page.locator('[data-qa="task-body"]')

    async def navigate(self):
        await self._page.goto(self.URL + "?vacancyId=" + self.id)

    async def _get_question_type(self, task: Locator) -> QuestionType:
        if await task.locator('input[type="radio"]').count() > 0:
            if await task.locator("textarea").count() > 0:
                return "radio+text"
            else:
                return "radio"
        elif await task.locator('input[type="checkbox"]').count() > 0:
            return "checkbox"
        elif await task.locator("textarea").count() > 0:
            return "text"
        raise ValueError("Unknown question type")

    async def get_questions(self) -> list[VacancyQuestion]:
        questions: list[VacancyQuestion] = []
        for task in await self.tasks.all():
            question = await task.locator('[data-qa="task-question"]').text_content()
            type = await self._get_question_type(task)

            if not question:
                continue

            # Gather all available options
            labels = await task.locator('label[data-qa="cell"]').all()
            options = [await option.text_content() or "N/A" for option in labels]

            match type:
                case "radio":
                    questions.append(RadioQuestion(question=question, options=options))
                case "radio+text":
                    questions.append(
                        RadioWithTextQuestion(question=question, options=options[:-1])
                    )
                case "checkbox":
                    questions.append(
                        CheckboxQuestion(question=question, options=options)
                    )
                case "text":
                    questions.append(TextQuestion(question=question))
                case _:
                    raise ValueError(
                        f"Unknown question type for task: {question}, on page: {self.URL + '?vacancyId=' + self.id}"
                    )

        return questions

    async def answer_questions(self, answers: list[VacancyQuestionAnswer]) -> None:
        for idx, answer in enumerate(answers):
            task = self.tasks.nth(idx)

            if answer.skip:
                continue

            match answer:
                case RadioAnswer(answer=answer):
                    option = task.locator('label[data-qa="cell"]').nth(answer)
                    await option.click()
                case RadioWithTextAnswer(answer=answer, option=option):
                    option_label = task.locator('label[data-qa="cell"]').nth(option)
                    await option_label.click()

                    if answer is not None:
                        option_label = task.locator('label[data-qa="cell"]').last
                        await option_label.click()

                        text_input = task.locator("textarea")
                        await text_input.clear()
                        await text_input.fill(answer)
                case TextAnswer(answer=answer):
                    text_input = task.locator("textarea")
                    await text_input.clear()
                    await text_input.fill(answer)
                case CheckboxAnswer(answer=answer):
                    for option in answer:
                        await task.locator('label[data-qa="cell"]').nth(option).click()
                case _:
                    raise ValueError(f"Unknown question type: {answer}")

    async def apply(self) -> None:
        submit_button = self._page.locator('[data-qa="vacancy-response-submit-popup"]')
        skip_button = self._page.locator(
            '[data-qa="vacancy-response-link-no-questions"]'
        )

        # Try to submit with questions
        # Fails if there are questions that need to be answered
        if await submit_button.is_visible():
            await submit_button.click()
            await self._page.wait_for_load_state("networkidle")

        # Try to submit without questions
        # Fails if the test is required
        if await skip_button.is_visible():
            await skip_button.click()
            await self._page.wait_for_load_state("networkidle")

        raise VacancyApplicationError(f"Failed to apply for vacancy {self.id}")

    async def attach_cover_letter(self, cover_letter: str) -> None:
        """Handle optional cover letter."""
        cover_letter_toggle = self._page.locator(
            '[data-qa="vacancy-response-letter-toggle"]'
        )
        cover_letter_input = self._page.locator(
            '[data-qa="vacancy-response-popup-form-letter-input"]'
        )

        if await cover_letter_toggle.is_visible():
            await cover_letter_toggle.click()
            await cover_letter_input.fill(cover_letter)


class VacancyPage(BasePage):
    URL = "https://hh.ru/vacancy"

    def __init__(
        self,
        page: Page,
        id: str,
    ):
        super().__init__(page)
        self.id = id

        self._get_cover_letter = None
        self._get_answers = None

        # Locators
        self.vacancy_title = page.locator('[data-qa="vacancy-title"]')
        self.vacancy_description = page.locator('[data-qa="vacancy-description"]')
        self.vacancy_chat = page.locator(
            '[data-qa="vacancy-response-link-view-topic"]'
        ).first
        self.apply_button = page.locator('[data-qa="vacancy-response-link-top"]').first

    async def navigate(self) -> None:
        await self._page.goto(self.URL + "/" + self.id)

    def set_cover_letter_generator(self, generator: CoverLetterGenerator) -> None:
        self._get_cover_letter = generator

    def set_answers_generator(self, generator: AnswersGenerator) -> None:
        self._get_answers = generator

    async def _parse_salary(self) -> str | None:
        vacancy_salary = self._page.locator('[data-qa="vacancy-salary"]')
        return (
            await vacancy_salary.text_content()
            if await vacancy_salary.is_visible()
            else None
        )

    async def _parse_experience(self) -> str | None:
        vacancy_experience = self._page.locator('[data-qa="vacancy-experience"]')
        return (
            await vacancy_experience.text_content()
            if await vacancy_experience.is_visible()
            else None
        )

    async def _parse_employment_form(self) -> str | None:
        vacancy_employment_form = self._page.locator(
            '[data-qa="common-employment-text"]'
        )
        return (
            await vacancy_employment_form.text_content()
            if await vacancy_employment_form.is_visible()
            else None
        )

    async def _parse_work_format(self) -> str | None:
        vacancy_work_format = self._page.locator('[data-qa="work-formats-text"]')
        return (
            await vacancy_work_format.text_content()
            if await vacancy_work_format.is_visible()
            else None
        )

    async def _parse_hiring_formats(self) -> str | None:
        vacancy_hiring_formats = self._page.locator(
            '[data-qa="vacancy-hiring-formats"]'
        )
        return (
            await vacancy_hiring_formats.text_content()
            if await vacancy_hiring_formats.is_visible()
            else None
        )

    async def _parse_work_schedule(self) -> str | None:
        vacancy_work_schedule = self._page.locator(
            '[data-qa="work-schedule-by-days-text"]'
        )
        return (
            await vacancy_work_schedule.text_content()
            if await vacancy_work_schedule.is_visible()
            else None
        )

    async def _parse_working_hours(self) -> str | None:
        vacancy_working_hours = self._page.locator('[data-qa="working-hours-text"]')
        return (
            await vacancy_working_hours.text_content()
            if await vacancy_working_hours.is_visible()
            else None
        )

    async def _parse_vacancy_status(self) -> VacancyStatus:
        vacancy_status_card = self._page.locator('[class^="card-content"]').first
        status = VacancyStatus.NEW

        if await vacancy_status_card.is_visible():
            status_string = await vacancy_status_card.text_content()
            if status_string == "Ваc пригласили":
                status = VacancyStatus.INTERVIEW
            elif status_string == "Вам отказали":
                status = VacancyStatus.REJECTED
            elif status_string == "Вы откликнулись":
                status = VacancyStatus.AWAITING

        return status

    async def get_vacancy_info(self) -> Vacancy:
        status = await self._parse_vacancy_status()

        if status != VacancyStatus.NEW or await self.vacancy_chat.is_visible():
            is_applied_to = True
        else:
            is_applied_to = False

        return Vacancy(
            title=await self.vacancy_title.text_content() or "",
            description=await self.vacancy_description.text_content() or "",
            work_format=await self._parse_work_format(),
            experience=await self._parse_experience(),
            salary=await self._parse_salary(),
            work_schedule=await self._parse_work_schedule(),
            hiring_formats=await self._parse_hiring_formats(),
            employment_form=await self._parse_employment_form(),
            working_hours=await self._parse_working_hours(),
            status=status,
            is_applied_to=is_applied_to,
        )

    async def _handle_relocation_warning(self):
        """Handle relocation warning."""
        if not settings.apply_with_relocation:
            return

        title = self._page.locator('[data-qa="relocation-warning-title"]')
        confirm_relocation_button = self._page.locator(
            '[data-qa="relocation-warning-confirm"]'
        )
        abort_relocation_button = self._page.locator(
            '[data-qa="relocation-warning-abort"]'
        )

        if await title.is_visible():
            if settings.apply_with_relocation:
                await confirm_relocation_button.click()
            else:
                await abort_relocation_button.click()
            await self._page.wait_for_load_state("networkidle")

    async def _handle_required_cover_letter(self, cover_letter: str):
        """Handle required cover letter."""
        if not settings.apply_with_cover_letter:
            return

        cover_letter_textarea = self._page.locator(
            '[data-qa="vacancy-response-popup-form-letter-input"]'
        )
        cover_letter_submit_button = self._page.locator(
            '[data-qa="vacancy-response-submit-popup"]'
        )

        if await cover_letter_textarea.is_visible():
            await cover_letter_textarea.fill(cover_letter)
            await cover_letter_submit_button.click()
            await self._page.wait_for_load_state("networkidle")

    async def _handle_questions_page(self, cover_letter: str, vacancy: Vacancy):
        """Handle questions page."""
        if not settings.apply_with_questions:
            return

        if urlsplit(self._page.url).path != f"/vacancy/{self.id}":
            questions_page = VacancyQuestionsPage(self._page, self.id)
            if settings.generate_questions and self._get_answers:
                questions = await questions_page.get_questions()
                answers = await self._get_answers(vacancy, questions)
                await questions_page.answer_questions(answers)

            if settings.apply_with_cover_letter:
                await questions_page.attach_cover_letter(cover_letter)

            await questions_page.apply()
            await self._page.wait_for_load_state("networkidle")

    async def _handle_optional_cover_letter(self, cover_letter: str):
        """Handle optional cover letter."""

        if not settings.apply_with_cover_letter:
            return

        cover_letter_wrapper = self._page.locator(
            '[data-qa="vacancy-response-letter-informer"]'
        )

        cover_letter_textarea = cover_letter_wrapper.locator("textarea")
        cover_letter_submit_button = cover_letter_wrapper.locator(
            '[data-qa="vacancy-response-letter-submit"]'
        )

        if await cover_letter_textarea.is_visible():
            await cover_letter_textarea.fill(cover_letter)
            await cover_letter_submit_button.click()
            await self._page.wait_for_load_state("networkidle")

    async def _handle_salary_popup(self):
        close_button = self._page.locator(
            '[data-qa="additional-data-collector__popup-close"]'
        )
        if await close_button.is_visible():
            await close_button.click()
            await self._page.wait_for_load_state("networkidle")

    async def apply(self):
        """Apply to the vacancy if not already applied."""
        # Vacancy is already applied to.
        vacancy = await self.get_vacancy_info()

        if vacancy.is_applied_to:
            return

        # Apply to the vacancy
        await self.apply_button.click()
        await self._page.wait_for_load_state("networkidle")

        cover_letter: str = ""
        if settings.apply_with_cover_letter:
            cover_letter = settings.default_cover_letter or ""

            if settings.generate_cover_letter and self._get_cover_letter:
                cover_letter = await self._get_cover_letter(vacancy)

        # 1. Relocation warning shown
        await self._handle_relocation_warning()
        # 2. Popup requiring cover letter shown
        await self._handle_required_cover_letter(cover_letter)
        # 3. Redirected to questions page
        await self._handle_questions_page(cover_letter, vacancy)

        await self._handle_optional_cover_letter(cover_letter)
