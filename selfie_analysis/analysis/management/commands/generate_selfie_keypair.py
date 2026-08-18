"""
셀카 업로드 하이브리드 암호화(analysis/crypto.py)에 쓸 RSA 키쌍을 생성한다.

    python manage.py generate_selfie_keypair

개인키는 이 서비스의 .env(SELFIE_UPLOAD_RSA_PRIVATE_KEY)에 넣고,
공개키는 클라이언트(모바일 앱) 팀에 전달해 AES 키를 감쌀 때 쓰게 한다.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "셀카 업로드 암호화용 RSA 키쌍(개인키/공개키)을 생성해 출력한다."

    def handle(self, *args, **options):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        self.stdout.write(self.style.WARNING("=== PRIVATE KEY (.env의 SELFIE_UPLOAD_RSA_PRIVATE_KEY, 절대 커밋 금지) ==="))
        self.stdout.write(private_pem)
        self.stdout.write(self.style.SUCCESS("=== PUBLIC KEY (클라이언트/모바일 앱 팀에 전달) ==="))
        self.stdout.write(public_pem)
