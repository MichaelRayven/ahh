from playwright.async_api import Page

from src.pages.base import BasePage


class AuthPage(BasePage):
    URL = "https://hh.ru/account/login?role=applicant"

    def __init__(self, page: Page):
        super().__init__(page)

    async def is_authenticated(self) -> bool:
        """Checks if the user is authenticated"""
        profile_button = self._page.locator('[data-qa="mainmenu_profileAndResumes"]')

        return await profile_button.is_visible()

    async def is_two_factor_code_wrong(self) -> bool:
        wrong_code_label = self._page.locator(
            '[data-qa="oauth-merge-by-code__code-error-wrong_code"]'
        )
        return await wrong_code_label.is_visible()

    async def is_captcha_visible(self) -> bool:
        captcha = self._page.locator('[data-qa="account-captcha-picture"]')
        return await captcha.is_visible()

    async def select_phone_credential(self):
        phone_credential_checkbox = self._page.locator(
            '[data-qa^="credential-type-PHONE"]'
        )
        await phone_credential_checkbox.locator("..").click()

    async def select_email_credential(self):
        email_credential_checkbox = self._page.locator(
            '[data-qa^="credential-type-EMAIL"]'
        )
        await email_credential_checkbox.locator("..").click()

    async def fill_phone_number(self, phone_number: str):
        phone_number_input = self._page.locator(
            '[data-qa="magritte-phone-input-national-number-input"]'
        )
        await phone_number_input.clear()
        await phone_number_input.type(phone_number)

    async def fill_email(self, email: str):
        email_input = self._page.locator('[data-qa="applicant-login-input-email"]')
        await email_input.clear()
        await email_input.type(email)

    async def fill_password(self, password: str):
        password_input = self._page.locator(
            '[data-qa="applicant-login-input-password"]'
        )
        await password_input.clear()
        await password_input.type(password)
        await password_input.press("Enter")

    async def fill_two_factor_code(self, code: str):
        two_factor_input = self._page.locator(
            '[data-qa="magritte-pincode-input-field"]'
        )
        await two_factor_input.clear()
        await two_factor_input.type(code)

    # Titles: "вход", "поиск работы", "введите код из письма/смс", "введите пароль"
    async def continue_to_login(self):
        title_heading = self._page.locator('[data-qa="title"]')
        continue_button = self._page.locator('[data-qa="submit-button"]')

        title = (await title_heading.text_content() or "").lower()
        if "вход" in title:
            await continue_button.click()
        elif "поиск работы" in title:
            return
        else:
            raise ValueError(f"Unexpected auth page state: title={title}")

    async def continue_with_password(self):
        title_heading = self._page.locator('[data-qa="title"]')
        change_credential_button = self._page.locator(
            '[data-qa="change-credential-button"]'
        )
        password_login_button = self._page.locator(
            '[data-qa="expand-login-by-password"]'
        )

        title = (await title_heading.text_content() or "").lower()
        if "код" in title:
            await change_credential_button.click()
            await password_login_button.click()
        elif "поиск работы" in title:
            await password_login_button.click()
        elif "пароль" in title:
            return
        else:
            raise ValueError(f"Unexpected auth page state: title={title}")

    async def continue_with_two_factor_code(self):
        title_heading = self._page.locator('[data-qa="title"]')
        two_factor_code_login_button = self._page.locator(
            '[data-qa="expand-login-by-code-text"]'
        )
        continue_button = self._page.locator('[data-qa="submit-button"]')

        title = (await title_heading.text_content() or "").lower()
        if "пароль" in title:
            await two_factor_code_login_button.click()
        elif "поиск работы" in title:
            await continue_button.click()
        elif "код" in title:
            return
        else:
            raise ValueError(f"Unexpected auth page state: title={title}")
