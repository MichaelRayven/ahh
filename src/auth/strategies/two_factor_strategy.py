from playwright.async_api import Page, TimeoutError

from src.auth.schemas import AccountDetails, TwoFactorDetails
from src.auth.strategies.authentication_strategy import AuthenticationStrategy


class TwoFactorAuthenticationStrategy(AuthenticationStrategy):
    def __init__(self, page: Page, account_details: AccountDetails) -> None:
        self._page = page
        self._account_details = account_details

    async def _is_authenticated(self) -> bool:
        """Checks if the user is authenticated"""
        profile_button_locator = self._page.locator(
            '[data-qa="mainmenu_profileAndResumes"]'
        )
        return await profile_button_locator.is_visible()

    async def authenticate(self):
        # Locator definitions
        login_locator = self._page.locator('[data-qa="account-signup-email"]')
        wrong_code_label_locator = self._page.locator(
            '[data-qa="oauth-merge-by-code__code-error-wrong_code"]'
        )
        two_factor_locator = self._page.locator(
            '[data-qa="magritte-pincode-input-field"]'
        )
        captcha_locator = self._page.locator('[data-qa="account-captcha-picture"]')

        # Wait for page load
        await self._page.goto("https://hh.ru/")

        if await self._is_authenticated():
            return

        # Auth logic
        await login_locator.fill(self._account_details.login)
        await login_locator.press("Enter")

        logged_in = False
        while not logged_in:
            try:
                await two_factor_locator.wait_for()

                two_factor_details = TwoFactorDetails(
                    two_factor_code=input("Please provide the code: ")
                )
                await two_factor_locator.fill(two_factor_details.two_factor_code)

                if await wrong_code_label_locator.is_visible():
                    two_factor_locator.clear()
                    print("Wrong code. Please try again.")
                    continue

                logged_in = True
            except TimeoutError:
                if await captcha_locator.is_visible():
                    print("Please complete captcha.")
                else:
                    raise TimeoutError("Two-factor authentication timed out.")

        await self._page.wait_for_load_state("networkidle", timeout=10000)
