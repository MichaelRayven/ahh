from playwright.async_api import Page

from src.pages.base import BasePage

from .schemas import SearchQuery


class SearchPage(BasePage):
    URL = "https://hh.ru/search/vacancy"

    def __init__(self, page: Page, query: SearchQuery = SearchQuery()):
        super().__init__(page)
        self._query = query

        # Locators
        self.current_page_link = page.locator(
            '[data-qa="pager-page"][aria-current="true"]'
        )
        self.last_page_link = page.locator('[data-qa="pager-page"]').last
        self.first_page_link = page.locator('[data-qa="pager-page"]').first
        self.next_page_link = page.locator('[data-qa="pager-next"]')
        self.prev_page_link = page.locator('[data-qa="pager-previous"]')

    def navigate(self):
        """Navigate to the page."""
        url = f"{self.URL}?{self._query.get_url_params()}"
        self._page.goto(url)

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
        return int(await self.current_page_link.text_content() or "0")

    async def get_page_count(self) -> int:
        return int(await self.last_page_link.text_content() or 0)

    async def go_to_last_page(self):
        """Navigate to the last page."""
        await self.last_page_link.click()

    async def go_to_first_page(self):
        """Navigate to the first page."""
        await self.first_page_link.click()

    async def go_to_next_page(self):
        """Navigate to the next page if available."""
        # Convert to 0-based index
        current_page = await self.get_current_page() - 1
        page_count = await self.get_page_count()

        if current_page + 1 >= page_count:
            return

        # Navigate to next page
        url = f"{self.URL}?{self._query.get_url_params(page=current_page + 1)}"
        await self._page.goto(url)

    async def go_to_prev_page(self):
        """Navigate to the previous page if available."""
        # Convert to 0-based index
        current_page = await self.get_current_page() - 1

        if current_page <= 0:
            return

        # Navigate to previous page
        url = f"{self.URL}?{self._query.get_url_params(page=current_page - 1)}"
        await self._page.goto(url)
