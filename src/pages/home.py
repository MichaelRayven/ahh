from src.pages.base import BasePage
from playwright.async_api import Page, Locator


class HomePage(BasePage):
    URL = "https://hh.ru/"

    def __init__(self, page: Page):
        super().__init__(page)

        # Locators
        self.search_input: Locator = page.locator('input[data-qa="search-input"]')
        self.search_button: Locator = page.locator('button[data-qa="search-button"]')
        self.advanced_search_link: Locator = page.locator(
            'a[data-qa="advanced-search"]'
        )
        self.login_button: Locator = page.locator('a[data-qa="login"]')
        self.create_resume_button: Locator = page.locator('a[data-qa="signup"]')

    async def search_jobs(self, query: str) -> None:
        """Enters a search query and submits the job search."""
        await self.search_input.fill(query)
        await self.search_button.click()

    async def go_to_advanced_search(self) -> None:
        """Navigates to the advanced search page."""
        await self.advanced_search_link.click()

    async def go_to_login(self) -> None:
        """Clicks the login button in the header navigates to the auth page."""
        await self.login_button.click()

    async def go_to_create_resume(self) -> None:
        """Clicks the create resume button."""
        await self.create_resume_button.click()

    async def get_search_input_value(self) -> str:
        """Returns the current value inside the search input."""
        return await self.search_input.input_value()
