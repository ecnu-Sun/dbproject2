import pytest
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access.book import BookDB
import uuid


class TestQueryOrders:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # 设置：准备数据和初始化条件
        self.seller_id = f"test_query_orders_seller_{uuid.uuid1()}"
        self.buyer_id = f"test_query_orders_buyer_{uuid.uuid1()}"
        self.store_id = f"test_query_orders_store_{uuid.uuid1()}"
        self.password = "password"

        # 注册卖家和买家
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

        yield
        # 清理：测试后清理操作（如果有需要）

    def test_query_orders_initially_empty(self):
        # 买家查询历史订单，应为空
        status_code, orders = self.buyer.query_orders()
        assert status_code == 200
        assert len(orders) == 0

    def test_query_orders_after_order_placed(self):
        # 买家下单并支付
        for book in self.books:
            order_code, order_id = self.buyer.new_order(self.store_id, [(book.id, 1)])
            assert order_code == 200
            fund_code = self.buyer.add_funds(999999)
            assert fund_code == 200
            payment_code = self.buyer.payment(order_id)
            assert payment_code == 200

        # 买家查询历史订单，应包含刚生成的订单
        status_code, orders = self.buyer.query_orders()
        assert status_code == 200
        assert len(orders) > 0
