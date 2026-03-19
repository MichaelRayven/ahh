from playwright.async_api import Page

from src.common.base_page import BasePage

from .schemas import SearchQuery


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


class SearchPage(BasePage):
    URL = "https://hh.ru/search/vacancy"

    def __init__(self, page: Page, query: SearchQuery = SearchQuery()):
        super().__init__(page)
        self._query = query

    async def navigate(self):
        """Navigate to the page."""
        url = f"{self.URL}?{self._query.get_url_params()}"
        await self._page.goto(url)

    def set_search_query(self, query: SearchQuery):
        self._query = query

    async def get_vacancies_page(self, page: int):
        """Returns vacancies for a specific search page. 0-based page index."""

        url = f"{self.URL}?{self._query.get_url_params(page=page)}"
        await self._page.goto(url)

        return await self._page.query_selector_all('[data-qa="serp-item__title"]')

    async def get_vacancies_all(self):
        """Returns all vacancies available for the search query."""

        await self.go_to_first_page()

        page_count = await self.get_page_count()
        vacancies = []

        for page in range(page_count):
            page_vacancies = await self.get_vacancies_page(page)
            vacancies.extend(page_vacancies)

        return vacancies

    async def get_current_page(self) -> int:
        current_page_link = self._page.locator(
            '[data-qa="pager-page"][aria-current="true"]'
        )
        return int(await current_page_link.text_content() or "0")

    async def get_page_count(self) -> int:
        last_page_link = self._page.locator('[data-qa="pager-page"]').last
        return int(await last_page_link.text_content() or "0")

    async def go_to_page(self, page: int):
        """Navigate to a specific page."""
        if page < 1 or page > await self.get_page_count():
            return

        url = f"{self.URL}?{self._query.get_url_params(page=page)}"
        await self._page.goto(url)

    async def go_to_last_page(self):
        """Navigate to the last page."""
        await self.go_to_page(await self.get_page_count())

    async def go_to_first_page(self):
        """Navigate to the first page."""
        await self.go_to_page(1)

    async def go_to_next_page(self):
        """Navigate to the next page if available."""
        # Convert to 0-based index
        current_page = await self.get_current_page()
        await self.go_to_page(current_page + 1)

    async def go_to_prev_page(self):
        """Navigate to the previous page if available."""
        # Convert to 0-based index
        current_page = await self.get_current_page()
        await self.go_to_page(current_page - 1)
