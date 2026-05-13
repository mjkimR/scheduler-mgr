from app.features.tasks import task
from app.features.tasks.core.log import logger


@task()
async def hello_world(message: str = "hello") -> None:
    """Example task. Registered as 'hello_world'."""
    logger.info(f"[hello_world] {message}")


@task(name="send_report")
async def send_report(recipient: str, report_type: str = "daily") -> None:
    """Example task. Registered as 'send_report'."""
    logger.info(f"[send_report] Sending {report_type} report to {recipient}")
