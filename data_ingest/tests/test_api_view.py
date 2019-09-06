from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ApiValidateTests(APITestCase):

    fixtures = ['test_data.json']

    def test_api_validate_json_empty_no_token(self):
        """
        Ensure it is unauthorized when we post to the API for validation without a token.
        """
        url = reverse('validate')
        data = []
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_validate_json_empty_with_token(self):
        """
        Ensure we can post to the API for validation with a token.
        """
        url = reverse('validate')
        data = []
        token = "this1s@t0k3n"
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
