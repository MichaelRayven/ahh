import phonenumbers
from playwright.async_api import Page

from src.auth.schemas import AccountDetails
from src.auth.strategies.authentication_strategy import AuthenticationStrategy


class PasswordAuthenticationStrategy(AuthenticationStrategy):
    def __init__(self, page: Page, account_details: AccountDetails) -> None:
        self._page = page
        self._account_details = account_details

    async def _is_authenticated(self) -> bool:
        """Checks if the user is authenticated"""
        profile_button_locator = self._page.locator(
            '[data-qa="mainmenu_profileAndResumes"]'
        )
        return await profile_button_locator.is_visible()

    async def _authenticate_with_phone(self):
        phone_chedential_type_check_locator = self._page.locator(
            '[data-qa^="credential-type-PHONE"]'
        )
        phone_number_input_locator = self._page.locator(
            '[data-qa="magritte-phone-input-national-number-input"]'
        )
        password_login_button = self._page.locator(
            '[data-qa="expand-login-by-password"]'
        )
        password_input = self._page.locator(
            '[data-qa="applicant-login-input-password"]'
        )

        # TODO: Choose country code

        data_qa = await phone_chedential_type_check_locator.get_attribute("data-qa")
        if "checked" not in (data_qa or ""):
            # Click on the parent element to toggle the checkbox
            await phone_chedential_type_check_locator.locator("..").click()

        phone_number = phonenumbers.parse(self._account_details.login)
        await phone_number_input_locator.clear()
        await phone_number_input_locator.type(str(phone_number.national_number))
        await password_login_button.click()

        assert self._account_details.password is not None
        await password_input.type(self._account_details.password)
        await password_input.press("Enter")

    async def _authenticate_with_email(self):
        email_chedential_type_check_locator = self._page.locator(
            '[data-qa^="credential-type-EMAIL"]'
        )
        email_input_locator = self._page.locator(
            '[data-qa="applicant-login-input-email"]'
        )
        password_login_button = self._page.locator(
            '[data-qa="expand-login-by-password"]'
        )
        password_input = self._page.locator(
            '[data-qa="applicant-login-input-password"]'
        )

        data_qa = await email_chedential_type_check_locator.get_attribute("data-qa")
        if "checked" not in (data_qa or ""):
            # Click on the parent element to toggle the checkbox
            await email_chedential_type_check_locator.locator("..").click()

        await email_input_locator.clear()
        await email_input_locator.type(self._account_details.login)
        await password_login_button.click()

        assert self._account_details.password is not None
        await password_input.type(self._account_details.password)
        await password_input.press("Enter")

    async def authenticate(self):
        submit_button_locator = self._page.locator('[data-qa="submit-button"]')

        # Wait for page load
        await self._page.goto("https://hh.ru/account/login?role=applicant")

        if await self._is_authenticated():
            return

        # Auth logic
        await submit_button_locator.click()

        if self._account_details.login_type == "phone":
            await self._authenticate_with_phone()
        else:
            await self._authenticate_with_email()

        await self._page.wait_for_load_state("networkidle")
