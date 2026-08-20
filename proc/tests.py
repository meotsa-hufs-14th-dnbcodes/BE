from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Category, Procedure, ProcedureRecord


class ProcedureRecordDetailViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="pw12345", nickname="owner", gender="F", age=25,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="pw12345", nickname="other", gender="M", age=30,
        )

        self.category = Category.objects.create(category_name="테스트카테고리")
        self.procedure = Procedure.objects.create(
            category=self.category, proc_code="TEST001", proc_name="테스트시술",
            proc_duration=1, reminder_duration_days=180,
        )

        self.record = ProcedureRecord.objects.create(
            user=self.user,
            procedure=self.procedure,
            proc_name="테스트시술",
            procedure_date="2026-01-01",
            hospital_name="기존병원",
            memo="기존메모",
        )

        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")

    def _url(self, record_id):
        return reverse('procedure-record-detail', kwargs={'record_id': record_id})

    def test_retrieve_own_record(self):
        response = self.client.get(self._url(self.record.record))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["recordId"], self.record.record)
        self.assertEqual(response.data["hospitalName"], "기존병원")

    def test_retrieve_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(self._url(self.record.record))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_another_users_record_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.create(user=self.other_user).key}")
        response = self.client.get(self._url(self.record.record))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_updates_only_given_fields(self):
        response = self.client.patch(
            self._url(self.record.record), {"hospitalName": "새의원", "memo": "붓기 있음"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(self.record.hospital_name, "새의원")
        self.assertEqual(self.record.memo, "붓기 있음")
        # procName을 안 보냈으니 기존 시술 코드가 그대로 유지되어야 함
        self.assertEqual(self.record.procedure_id, self.procedure.proc_code)
        self.assertEqual(self.record.proc_name, "테스트시술")

    def test_patch_changing_proc_name_relinks_procedure(self):
        other_category = Category.objects.create(category_name="다른카테고리")
        other_procedure = Procedure.objects.create(
            category=other_category, proc_code="TEST002", proc_name="다른시술",
            proc_duration=3, reminder_duration_days=90,
        )

        response = self.client.patch(
            self._url(self.record.record), {"procName": "다른시술"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(self.record.procedure_id, other_procedure.proc_code)
        self.assertEqual(self.record.proc_name, "다른시술")

    def test_patch_future_date_rejected(self):
        response = self.client.patch(
            self._url(self.record.record), {"procedureDate": "2999-01-01"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_full_update(self):
        response = self.client.put(
            self._url(self.record.record),
            {
                "procName": "테스트시술",
                "procedureDate": "2026-02-01",
                "hospitalName": "풀업데이트병원",
                "memo": "전체 수정",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(str(self.record.procedure_date), "2026-02-01")
        self.assertEqual(self.record.hospital_name, "풀업데이트병원")
        self.assertEqual(self.record.memo, "전체 수정")

    def test_cannot_update_another_users_record(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.create(user=self.other_user).key}")
        response = self.client.patch(
            self._url(self.record.record), {"hospitalName": "해킹시도"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_requires_authentication(self):
        self.client.credentials()
        response = self.client.patch(
            self._url(self.record.record), {"hospitalName": "새의원"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_soft_deletes_record(self):
        response = self.client.delete(self._url(self.record.record))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["recordId"], self.record.record)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_deleted)

    def test_delete_already_deleted_record_returns_404(self):
        self.record.is_deleted = True
        self.record.save(update_fields=['is_deleted'])

        response = self.client.delete(self._url(self.record.record))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_delete_another_users_record(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.create(user=self.other_user).key}")
        response = self.client.delete(self._url(self.record.record))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_requires_authentication(self):
        self.client.credentials()
        response = self.client.delete(self._url(self.record.record))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
