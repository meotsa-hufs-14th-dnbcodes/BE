import logging

logger = logging.getLogger(__name__)


def notify_analysis_done(user_id, status, fail_reason=None):
    """
    TODO: 알림 시스템(벨아이콘/알림함, ANALYSIS_DONE 타입) 완성되면 해당 호출로 교체합니다.
    지금은 웹훅이 제대로 도착하는지만 확인하기 위한 로그입니다.
    """
    logger.info(
        "analysis done: user_id=%s status=%s fail_reason=%s",
        user_id, status, fail_reason,
    )
