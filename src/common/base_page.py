from playwright.async_api import Page


class BasePage:
    URL = ""

    def __init__(self, page: Page):
        self._page = page

    async def navigate(self) -> None:
        """Navigates to the page."""
        await self._page.goto(self.URL)
