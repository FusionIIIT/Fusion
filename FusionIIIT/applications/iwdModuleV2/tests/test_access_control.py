from applications.filetracking.models import File
from applications.globals.models import Designation
from applications.iwdModuleV2.tests.conftest import BaseModuleTestCase


class IwdAccessControlTests(BaseModuleTestCase):
    def _make_file(self, uploader, src_module='IWD'):
        designation = Designation.objects.get(name='Electrical_AE')
        return File.objects.create(
            uploader=uploader,
            designation=designation,
            subject='Access control test',
            src_module=src_module,
            src_object_id='access-control-test',
            file_extra_JSON={},
        )

    def test_view_file_hides_files_from_other_modules(self):
        file_obj = self._make_file(self.extra_worker, src_module='another-module')
        self.login_as_worker()

        response = self.api_get('view-file/', {'file_id': file_obj.id}, expected_status=404)

        self.assertEqual(response.data['code'], 'FILE_NOT_FOUND')

    def test_view_file_hides_iwd_files_from_unrelated_users(self):
        file_obj = self._make_file(self.extra_adm)
        self.login_as_worker()

        response = self.api_get('view-file/', {'file_id': file_obj.id}, expected_status=404)

        self.assertEqual(response.data['code'], 'FILE_NOT_FOUND')

    def test_uploader_can_view_own_iwd_file(self):
        file_obj = self._make_file(self.extra_worker)
        self.login_as_worker()

        response = self.api_get('view-file/', {'file_id': file_obj.id}, expected_status=200)

        self.assertEqual(response.data['file']['id'], file_obj.id)

    def test_worker_cannot_select_auditor_role_for_audit_list(self):
        self.login_as_worker()

        self.api_get('audit-document-view/', {'role': 'Auditor'}, expected_status=403)

    def test_worker_cannot_read_generated_bills(self):
        self.login_as_worker()

        self.api_get('generated-bills-view/', expected_status=403)

    def test_worker_cannot_generate_or_read_bill_pdf(self):
        self.login_as_worker()

        self.api_get('generate-bill-pdf/', {'request_id': '1'}, expected_status=403)

    def test_worker_cannot_settle_bills_by_claiming_accounts_role(self):
        self.login_as_worker()

        self.api_get('settle-bills-view/', {'role': 'Accounts Admin'}, expected_status=403)
