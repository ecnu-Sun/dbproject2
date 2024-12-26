import pytest
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access.book import BookDB
import uuid


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Set up necessary data before test
        self.seller_id = f"test_cancel_order_seller_{uuid.uuid1()}"
        self.buyer_id = f"test_cancel_order_buyer_{uuid.uuid1()}"
        self.store_id = f"test_cancel_order_store_{uuid.uuid1()}"
        self.password = "password"

        # Register new seller and buyer
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # Seller creates store and adds books
        store_creation_code = self.seller.create_store(self.store_id)
        assert store_creation_code == 200

        book_db = BookDB(True)
        self.books = book_db.get_book_info(0, 1)

        # Add books to store
        for book in self.books:
            add_book_code = self.seller.add_book(self.store_id, 10, book)
            assert add_book_code == 200

        yield
        # Cleanup after tests if necessary

    def test_cancel_order(self):
        # Buyer places an order but does not pay
        for book in self.books:
            order_code, order_id = self.buyer.new_order(self.store_id, [(book.id, 1)])
            assert order_code == 200

            # Buyer cancels the order
            cancel_code = self.buyer.cancel_order(order_id)
            assert cancel_code == 200
