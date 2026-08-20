import requests
from django.conf import settings


class SelfieAnalysisError(Exception):
    pass


def _headers():
    return {"X-Service-Token": settings.INTERNAL_SERVICE_TOKEN}


def create_analysis(user_id, captured_at, image):
    resp = requests.post(
        f"{settings.SELFIE_ANALYSIS_BASE_URL}/api/v1/selfie-analyses/",
        json={
            "user_id": user_id,
            "captured_at": captured_at,
            "image": image,
        },
        headers=_headers(),
        timeout=5,
    )
    if resp.status_code != 202:
        raise SelfieAnalysisError(f"unexpected status {resp.status_code}: {resp.text}")
    return resp.json()



def get_analysis(analysis_id):
    resp = requests.get(
        f"{settings.SELFIE_ANALYSIS_BASE_URL}/api/v1/selfie-analyses/{analysis_id}/",
        headers=_headers(),
        timeout=5,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()
