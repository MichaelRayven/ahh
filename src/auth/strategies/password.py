import phonenumbers
from src.auth.pages import AuthPage
from src.auth.schemas import AccountDetails
from src.auth.strategies.base import AuthenticationStrategy


class PasswordAuthenticationStrategy(AuthenticationStrategy):
    def __init__(self, auth_page: AuthPage, account_details: AccountDetails) -> None:
        self._auth_page = auth_page
        self._account_details = account_details

    async def _authenticate_with_phone(self):
        # TODO: Choose country code
        assert self._account_details.password is not None

        await self._auth_page.select_phone_credential()

        phone_number = phonenumbers.parse(self._account_details.login)
        await self._auth_page.fill_phone_number(str(phone_number.national_number))
        await self._auth_page.continue_with_password()

        await self._auth_page.fill_password(self._account_details.password)

    async def _authenticate_with_email(self):
        assert self._account_details.password is not None

        await self._auth_page.select_email_credential()

        await self._auth_page.fill_email(self._account_details.login)
        await self._auth_page.continue_with_password()

        await self._auth_page.fill_password(self._account_details.password)

    async def authenticate(self):
        # Wait for page load
        await self._auth_page.navigate()

        if await self._auth_page.is_authenticated():
            return

        # Auth logic
        await self._auth_page.continue_to_login()

        if self._account_details.login_type == "phone":
            await self._authenticate_with_phone()
        else:
            await self._authenticate_with_email()
