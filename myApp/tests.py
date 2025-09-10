from django.test import TestCase
from .models import Contact
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import io


class TestModel(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='user', password='password')
        self.contact = Contact.objects.create(
            name='testname',
            phone_number ='+905391111111',
            email='test@example.com',
            address='test street',
            author=self.user,)

    def test_create_a_contact(self):
        self.assertEqual(self.contact.name, 'testname')
        self.assertEqual(self.contact.email, 'test@example.com')
        self.assertEqual(self.contact.phone_number, '+905391111111')
        self.assertEqual(self.contact.address, 'test street')

    def test_authenticated_user_have_access_to_contact_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('myApp:contact_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.contact, response.context['contacts'])

    def test_unauthenticated_user_no_access_to_contactlist(self):
        self.client.logout()
        response = self.client.get(reverse('myApp:contact_list'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


class TestContactExportImport(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='user', password='password')
        self.client.force_authenticate(self.user)

    def test_export_csv_returns_file_path_mesage(self):
        # api is the app_name
        # contacts is the basename
        # export_csv is the action method for the viewset
        # so the rever url is : 'api:contacts-export-csv'
        response = self.client.get(reverse('api:contacts-export-csv'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('your file has been created', response.data.lower())

    def test_import_csv_valid_file(self):
        csv_content = "name,phone_number,email,address\nTest,+905391111111,test@example.com,Test St"
        file = io.StringIO(csv_content)
        file.name = 'test.csv'

        url = reverse('api:contacts-import-csv')
        response = self.client.post(url, {'my_file': file}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn('imported successfully', response.data['success'.lower()])

    def test_import_csv_with_invalid_file(self):
        file = io.StringIO("bad data")
        file.name = 'not_a_csv.txt'

        url = reverse('api:contacts-import-csv')
        response = self.client.post(url, {'my_file': file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('please upload a valid csv file', response.data['error'].lower())