import logging

from notifications import services as notification_services

logger = logging.getLogger(__name__)


def notify_analysis_done(user_id, status, fail_reason=None):
    logger.info(
        "analysis done: user_id=%s status=%s fail_reason=%s",
        user_id, status, fail_reason,
    )
    notification_services.notify_selfie_analysis_done(
        user_id=user_id, status=status, fail_reason=fail_reason,
    )
