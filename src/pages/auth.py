from playwright.async_api import Locator, Page

from src.pages.base import BasePage


class AuthPage(BasePage):
    URL = "https://hh.ru/account/login"

    def __init__(self, page: Page):
        super().__init__(page)

        self.awaiting_two_factor_code = False

        # Locators
        self.phone_input: Locator = page.locator(
            '[data-qa="magritte-phone-input-national-number-input"]'
        )
        self.email_input: Locator = page.locator(
            '[data-qa="applicant-login-input-email"]'
        )
        self.submit_button: Locator = page.locator('[data-qa="submit-button"]')
        self.email_login_option: Locator = page.locator(
            '[data-qa^="credential-type-EMAIL"]'
        )
        self.phone_login_option: Locator = page.locator(
            '[data-qa^="credential-type-PHONE"]'
        )
        self.two_factor_input: Locator = page.locator(
            '[data-qa="magritte-pincode-input-field"]'
        )
        self.two_factor_resend_button: Locator = page.locator(
            '[data-qa="applicant-login-button-code-sender"]'
        )
        self.password_login_button: Locator = page.locator(
            '[data-qa="expand-login-by-password"]'
        )
        self.password_input: Locator = page.locator(
            '[data-qa="applicant-login-input-password"]'
        )

    async def login_by_phone(self, phone: str) -> None:
        """Logs in using a phone number."""
        await self.navigate()
        # Check if phone login is selected
        checked = await self.phone_login_option.get_attribute("data-qa")
        if "checked" not in (checked or ""):
            await self.phone_login_option.click()

        await self.phone_input.clear()
        await self.phone_input.fill(phone)
        await self.submit_button.click()

    async def login_by_email(self, email: str) -> None:
        """Logs in using an email address."""
        await self.navigate()
        # Check if email login is selected
        checked = await self.email_login_option.get_attribute("data-qa")
        if "checked" not in (checked or ""):
            await self.email_login_option.click()

        await self.email_input.clear()
        await self.email_input.fill(email)
        await self.submit_button.click()
        self.awaiting_two_factor_code = True

    async def fill_two_factor_code(self, code: str) -> None:
        """Fills the two-factor authentication code."""
        if await self.two_factor_input.is_visible():
            await self.two_factor_input.fill(code)

    async def resend_two_factor(self) -> None:
        """Resend the two-factor authentication code."""
        if await self.two_factor_resend_button.is_visible():
            await self.two_factor_resend_button.click()

    async def login_by_phone_with_password(self, phone: str, password: str) -> None:
        """Logs in using a phone number and password."""
        await self.navigate()
        # Check if phone login is selected
        checked = await self.phone_login_option.get_attribute("data-qa")
        if "checked" not in (checked or ""):
            await self.phone_login_option.click()

        await self.phone_input.clear()
        await self.phone_input.fill(phone)
        await self.password_login_button.click()

        await self.password_input.clear()
        await self.password_input.fill(password)
        await self.submit_button.click()

    async def login_by_email_with_password(self, email: str, password: str) -> None:
        """Logs in using an email address and password."""
        await self.navigate()
        # Check if email login is selected
        checked = await self.email_login_option.get_attribute("data-qa")
        if "checked" not in (checked or ""):
            await self.email_login_option.click()

        await self.email_input.clear()
        await self.email_input.fill(email)
        await self.password_login_button.click()

        await self.password_input.clear()
        await self.password_input.fill(password)
        await self.submit_button.click()
