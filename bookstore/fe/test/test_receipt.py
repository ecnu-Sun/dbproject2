import pytest
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access.book import BookDB
import uuid


class TestConfirmReceipt:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # 设置：准备数据和初始化条件
        self.seller_id = f"test_confirm_receipt_seller_{uuid.uuid1()}"
        self.buyer_id = f"test_confirm_receipt_buyer_{uuid.uuid1()}"
        self.store_id = f"test_confirm_receipt_store_{uuid.uuid1()}"
        self.password = "password"

        # 注册新卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 卖家创建店铺并添加书籍
        store_creation_code = self.seller.create_store(self.store_id)
        assert store_creation_code == 200

        # 获取书籍信息
        book_db = BookDB(True)
        self.books = book_db.get_book_info(0, 1)

        # 卖家向店铺添加书籍
        for book in self.books:
            add_book_code = self.seller.add_book(self.store_id, 10, book)
            assert add_book_code == 200

        # 买家下单并支付
        self.order_id = None
        for book in self.books:
            order_code, self.order_id = self.buyer.new_order(self.store_id, [(book.id, 1)])
            assert order_code == 200

        # 买家充值并支付订单
        fund_code = self.buyer.add_funds(999999)
        assert fund_code == 200

        payment_code = self.buyer.payment(self.order_id)
        assert payment_code == 200

        # 卖家确认发货
        shipping_code = self.seller.confirm_shipping(self.seller_id, self.order_id)
        assert shipping_code == 200

        yield
        # 清理：测试后清理操作（如果有需要）

    def test_confirm_receipt_success(self):
        # 买家确认收货
        receipt_code = self.buyer.confirm_receipt(self.order_id)
        assert receipt_code == 200

    def test_confirm_receipt_non_existent_order(self):
        # 买家尝试确认收货一个不存在的订单
        invalid_order_id = self.order_id + "_x"
        receipt_code = self.buyer.confirm_receipt(invalid_order_id)
        assert receipt_code != 200
