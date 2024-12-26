import requests
import simplejson
from urllib.parse import urljoin
from fe.access.auth import Auth


class Customer:
    def __init__(self, base_url, user_identifier, user_password):
        self.base_url = urljoin(base_url, "buyer/")
        self.user_identifier = user_identifier
        self.user_password = user_password
        self.auth_token = ""
        self.device_info = "my terminal"
        self.authentication = Auth(base_url)
        status_code, self.auth_token = self.authentication.login(self.user_identifier, self.user_password, self.device_info)
        assert status_code == 200

    def place_order(self, store_identifier: str, items: [(str, int)]) -> (int, str):
        order_items = [{"id": item[0], "count": item[1]} for item in items]
        request_data = {"user_id": self.user_identifier, "store_id": store_identifier, "books": order_items}
        url = urljoin(self.base_url, "new_order")
        headers = {"token": self.auth_token}
        response = requests.post(url, headers=headers, json=request_data)
        response_data = response.json()
        return response.status_code, response_data.get("order_id")

    def process_payment(self, order_identifier: str):
        request_data = {
            "user_id": self.user_identifier,
            "password": self.user_password,
            "order_id": order_identifier,
        }
        url = urljoin(self.base_url, "payment")
        headers = {"token": self.auth_token}
        response = requests.post(url, headers=headers, json=request_data)
        return response.status_code

    def add_balance(self, amount: str) -> int:
        request_data = {
            "user_id": self.user_identifier,
            "password": self.user_password,
            "add_value": amount,
        }
        url = urljoin(self.base_url, "add_funds")
        headers = {"token": self.auth_token}
        response = requests.post(url, headers=headers, json=request_data)
        return response.status_code

    def confirm_order_receipt(self, order_identifier: str) -> int:
        """
        Confirm receipt of an order
        :param order_identifier: The ID of the order
        :return: HTTP status code
        """
        request_data = {
            "user_id": self.user_identifier,
            "order_id": order_identifier,
        }
        url = urljoin(self.base_url, "confirm_receipt")
        headers = {"token": self.auth_token}
        response = requests.post(url, headers=headers, json=request_data)
        return response.status_code

    def retrieve_orders(self) -> (int, list):
        """
        Retrieve the user's order history
        :return: HTTP status code and order list (if successful)
        """
        url = urljoin(self.base_url, f"query_orders?user_id={self.user_identifier}")
        headers = {"token": self.auth_token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.status_code, response.json().get("orders", [])
        return response.status_code, []

    def revoke_order(self, order_identifier: str) -> int:
        """
        Cancel an order
        :param order_identifier: The ID of the order
        :return: HTTP status code
        """
        request_data = {
            "user_id": self.user_identifier,
            "order_id": order_identifier,
        }
        url = urljoin(self.base_url, "cancel_order")
        headers = {"token": self.auth_token}
        response = requests.post(url, headers=headers, json=request_data)
        return response.status_code
