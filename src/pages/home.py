from playwright.async_api import Page

from src.pages.base import BasePage


class HomePage(BasePage):
    URL = "https://hh.ru/"

    def __init__(self, page: Page):
        super().__init__(page)

    async def search_jobs(self, query: str) -> None:
        """Enters a search query and submits the job search."""
        search_input = self._page.locator('input[data-qa="search-input"]')
        search_button = self._page.locator('button[data-qa="search-button"]')

        await search_input.fill(query)
        await search_button.click()

    async def go_to_advanced_search(self) -> None:
        """Navigates to the advanced search page."""
        advanced_search_link = self._page.locator('a[data-qa="advanced-search"]')
        await advanced_search_link.click()

    async def go_to_login(self) -> None:
        """Clicks the login button in the header navigates to the auth page."""
        login_button = self._page.locator('a[data-qa="login"]')
        await login_button.click()

    async def go_to_create_resume(self) -> None:
        """Clicks the create resume button."""
        create_resume_button = self._page.locator('a[data-qa="signup"]')
        await create_resume_button.click()
