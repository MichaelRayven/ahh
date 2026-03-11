import asyncio
import logging
from os import path

from playwright.async_api import async_playwright

from src.auth.strategies.authentication_strategy import AuthenticationStrategy
from src.auth.strategies.password_strategy import PasswordAuthenticationStrategy
from src.auth.strategies.two_factor_strategy import TwoFactorAuthenticationStrategy
from src.config.settings import get_app_settings
from src.tasks.auto_apply import AutoApplyTask

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=False)
        settings = get_app_settings()
        # Load context from state
        if path.exists(settings.state_path):
            context = await browser.new_context(storage_state=settings.state_path)
        else:
            context = await browser.new_context()

        page = await context.new_page()
        page.set_default_timeout(settings.default_timeout)

        # Authenticate
        if settings.credentials.password is None:
            auth_strategy: AuthenticationStrategy = TwoFactorAuthenticationStrategy(
                page=page,
                account_details=settings.credentials,
            )
        else:
            auth_strategy: AuthenticationStrategy = PasswordAuthenticationStrategy(
                page=page,
                account_details=settings.credentials,
            )
        await auth_strategy.authenticate()

        # Save browser context (to reuse sessions)
        await context.storage_state(path=settings.state_path)

        auto_apply = AutoApplyTask(context)
        await auto_apply.run()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
