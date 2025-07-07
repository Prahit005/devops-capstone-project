"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()
        talisman.force_https = False

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        # Create a test account
        account_data = {
            "name": "John Doe",
            "email": "john@doe.com",
            "address": "123 Main St.",
            "phone_number": "555-1212"
        }
        response = self.client.post("/accounts", json=account_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Extract account ID
        account_id = response.get_json()["id"]

        # Read the account back
        response = self.client.get(f"/accounts/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["name"], account_data["name"])
        self.assertEqual(data["email"], account_data["email"])
        self.assertEqual(data["address"], account_data["address"])
        self.assertEqual(data["phone_number"], account_data["phone_number"])

    def test_update_an_account(self):
        # Create an account
        account_data = {
            "name": "John Doe",
            "email": "john@doe.com",
            "address": "123 Main St.",
            "phone_number": "555-1212"
        }
        create_resp = self.client.post("/accounts", json=account_data)
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)

        account_id = create_resp.get_json()["id"]

        # New data for update
        updated_data = {
            "name": "John Updated",
            "email": "john@doe.com",
            "address": "456 Elm St.",
            "phone_number": "555-1111"
        }

        # Send PUT request to update account
        update_resp = self.client.put(f"/accounts/{account_id}", json=updated_data)
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        updated_account = update_resp.get_json()
        self.assertEqual(updated_account["name"], updated_data["name"])
        self.assertEqual(updated_account["address"], updated_data["address"])
        self.assertEqual(updated_account["phone_number"], updated_data["phone_number"])

    def test_delete_an_account(self):
        # Create a test account
        account_data = {
            "name": "Delete Me",
            "email": "deleteme@example.com",
            "address": "123 Gone St.",
            "phone_number": "555-0000"
        }
        create_resp = self.client.post("/accounts", json=account_data)
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)

        account_id = create_resp.get_json()["id"]

        # Delete the account
        delete_resp = self.client.delete(f"/accounts/{account_id}")
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)

        # Try to get the deleted account
        get_resp = self.client.get(f"/accounts/{account_id}")
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_all_accounts(self):
        # Create two test accounts
        account_data_1 = {
            "name": "User One",
            "email": "user1@example.com",
            "address": "123 Main St.",
            "phone_number": "555-1111"
        }
        account_data_2 = {
            "name": "User Two",
            "email": "user2@example.com",
            "address": "456 Oak St.",
            "phone_number": "555-2222"
        }

        self.client.post("/accounts", json=account_data_1)
        self.client.post("/accounts", json=account_data_2)

        # List all accounts
        response = self.client.get("/accounts")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

