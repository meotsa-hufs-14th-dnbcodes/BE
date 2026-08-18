"""
클라이언트 → 마이크로서비스 셀카 업로드용 하이브리드 복호화.

계약(클라이언트 구현 시 그대로 따라야 함):
  1. 클라이언트가 매 업로드마다 무작위 AES-256 키 + 12바이트 nonce를 생성한다.
  2. AES-256-GCM으로 원본 이미지를 암호화한다 (연산 결과에 16바이트 tag가 자동으로 붙는다 —
     `cryptography`의 AESGCM.encrypt()는 ciphertext+tag를 이어 붙여 반환한다).
  3. 이 마이크로서비스가 공개하는 RSA 공개키로 AES 키를 RSA-OAEP(SHA-256)로 감싼다.
  4. 아래 세 값을 base64로 인코딩해 업로드 요청 본문에 담는다:
       - encrypted_key  (RSA-OAEP로 감싼 AES 키)
       - nonce          (AES-GCM nonce, 12바이트)
       - ciphertext     (AES-GCM 암호문 + tag)

서버는 원본 이미지를 절대 디스크/DB에 저장하지 않는다. 복호화된 바이트는 Celery task
안에서만 메모리에 존재하고, 벤더 업로드가 끝나면 즉시 참조를 버린다(process 종료 시 GC).
"""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class DecryptionError(ValueError):
    """업로드된 셀카 payload를 복호화하지 못했을 때. 업로드 실패 예외 처리로 이어진다."""


def _load_private_key():
    pem = settings.SELFIE_UPLOAD_RSA_PRIVATE_KEY
    if not pem:
        raise DecryptionError("SELFIE_UPLOAD_RSA_PRIVATE_KEY가 설정되지 않았습니다.")
    return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)


def decrypt_selfie_payload(
    encrypted_key_b64: str, nonce_b64: str, ciphertext_b64: str
) -> bytes:
    """클라이언트가 보낸 base64 필드 3개를 원본 이미지 바이트로 복원"""

    try:
        encrypted_key = base64.b64decode(encrypted_key_b64)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
    except Exception as exc:  # base64 디코딩 실패 등
        raise DecryptionError(f"payload base64 디코딩 실패: {exc}") from exc

    private_key = _load_private_key()

    try:
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise DecryptionError(f"AES 키 언랩 실패: {exc}") from exc

    try:
        return AESGCM(aes_key).decrypt(nonce, ciphertext, associated_data=None)
    except Exception as exc:
        raise DecryptionError(f"AES-GCM 복호화 실패: {exc}") from exc
