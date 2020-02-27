from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import DefaultUpload
from ..api_views import UploadViewSet
from ..urls import router

import json


User = get_user_model()


class ApiValidateTests(APITestCase):

    fixtures = ["test_data.json"]

    def test_api_validate_json_empty_no_token(self):
        """
        Ensure it is unauthorized when we post to the API for validation without a token.
        """
        url = reverse("validate")
        data = []
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_validate_json_empty_with_token(self):
        """
        Ensure we can post to the API for validation with a token.
        """
        url = reverse("validate")
        data = []
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_delete_instance(self):
        """
        Soft delete an instance.
        """
        submitter = User.objects.first()
        DefaultUpload(submitter_id=submitter.pk).save()
        self.assertEqual(DefaultUpload.objects.count(), 1)
        instance = DefaultUpload.objects.first()
        view = UploadViewSet()
        view.basename = router.get_default_basename(UploadViewSet)
        view.request = None
        url = view.reverse_action("detail", args=[instance.pk])
        data = []
        token = "this1s@t0k3n"
        self.assertEqual(instance.status, "LOADING")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.delete(url, data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DefaultUpload.objects.count(), 1)
        instance = DefaultUpload.objects.first()
        self.assertEqual(instance.status, "DELETED")

    def test_api_delete_404(self):
        """
        Make sure we cannot delete a non-existent instance.
        """
        view = UploadViewSet()
        view.basename = router.get_default_basename(UploadViewSet)
        view.request = None
        url = view.reverse_action("detail", args=["99"])
        data = []
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.delete(url, data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_create_empty(self):
        view = UploadViewSet()
        view.basename = router.get_default_basename(UploadViewSet)
        view.request = None
        url = view.reverse_action("list", args=[])
        data = b"header1,header2,header3"
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(url, data, content_type="text/csv")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(json.loads(response.content)["valid"])

    def test_api_create_csv_example(self):
        view = UploadViewSet()
        view.basename = router.get_default_basename(UploadViewSet)
        view.request = None
        url = view.reverse_action("list", args=[])
        data = b'"Name","Title","level"\n"Guido","BDFL",20\n\n"Catherine",,9,"DBA"\n,\n"Tony","Engineer",10\n'
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(url, data, content_type="text/csv")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["tables"]), 1)
        self.assertEqual(result["tables"][0]["invalid_row_count"], 3)
        self.assertEqual(result["tables"][0]["valid_row_count"], 2)
        self.assertEqual(result["tables"][0]["whole_table_errors"], [])

    def test_api_create_error_handling(self):
        """
        Make sure we handle malformed input when creating an instance.
        """
        view = UploadViewSet()
        view.basename = router.get_default_basename(UploadViewSet)
        view.request = None
        url = view.reverse_action("list", args=[])
        data = "{foo}"
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content),
            {
                "detail": "JSON parse error - Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
            },
        )
