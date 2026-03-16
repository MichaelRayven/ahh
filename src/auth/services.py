import logging
from os import path

from playwright.async_api import Browser, BrowserContext

from src.config.settings import get_app_settings
from src.auth.strategies.base import AuthenticationStrategy
from src.auth.strategies.password import PasswordAuthenticationStrategy
from src.auth.strategies.two_factor import TwoFactorAuthenticationStrategy
from src.auth.pages import AuthPage

logger = logging.getLogger(__name__)
settings = get_app_settings()


class AuthService:
    def __init__(self, browser: Browser):
        self.browser = browser

    async def get_authenticated_context(self) -> BrowserContext:
        """
        Creates or loads a browser context, authenticates if necessary,
        and saves the state for subsequent usage.
        """
        # Load context from state
        if path.exists(settings.state_path):
            logger.info("Loading existing browser context from state.")
            context = await self.browser.new_context(storage_state=settings.state_path)
        else:
            logger.info("Creating new browser context.")
            context = await self.browser.new_context()

        page = await context.new_page()
        page.set_default_timeout(settings.default_timeout)

        # Build Page Object
        auth_page = AuthPage(page)

        # Wait for page load and check authentication status
        await auth_page.navigate()
        if await auth_page.is_authenticated():
            logger.info("User is already authenticated.")
            await page.close()
            return context

        logger.info("User is not authenticated. Starting authentication ...")

        # Fallback to chosen Strategy if needed
        credentials = settings.credentials
        if credentials.password is None:
            logger.info("Using Two-Factor Authentication.")
            auth_strategy: AuthenticationStrategy = TwoFactorAuthenticationStrategy(
                auth_page=auth_page,
                account_details=credentials,
            )
        else:
            logger.info("Using Password Authentication.")
            auth_strategy: AuthenticationStrategy = PasswordAuthenticationStrategy(
                auth_page=auth_page,
                account_details=credentials,
            )

        await auth_strategy.authenticate()

        # We assume authenticate succeeded at this point
        logger.info("Authentication complete. Saving context ...")
        await page.close()

        # Save browser context (to reuse sessions)
        await context.storage_state(path=settings.state_path)

        return context
