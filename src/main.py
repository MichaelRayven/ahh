import asyncio
import logging
from playwright.async_api import async_playwright
from src.tasks.auto_apply import AutoApplyTask
from src.auth.services import AuthService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=False)

        auth_service = AuthService(browser)
        context = await auth_service.get_authenticated_context()

        auto_apply = AutoApplyTask(context)
        await auto_apply.run()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
