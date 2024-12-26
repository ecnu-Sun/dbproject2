import psycopg2
from psycopg2 import errors
import uuid
import json
import logging
from be.model import db_conn
from be.model import error


class CustomerOrder(db_conn.DBConn):
    def __init__(self):
        super().__init__()

    def create_order(self, user_id: str, store_id: str, items: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            # 验证用户是否存在
            if not self._verify_user(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            # 验证商店是否存在
            if not self._verify_store(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成新的订单ID
            new_order_id = f"{user_id}_{store_id}_{uuid.uuid1()}"
            cursor = self.conn.cursor()

            # 开始创建新订单事务
            cursor.execute(
                "INSERT INTO new_order(order_id, store_id, user_id, status) "
                "VALUES(%s, %s, %s, %s);",
                (new_order_id, store_id, user_id, "unpaid"),
            )

            total_amount = 0
            for product_id, quantity in items:
                # 查询商品信息
                cursor.execute(
                    "SELECT book_id, stock_level, book_info FROM store "
                    "WHERE store_id = %s AND book_id = %s;",
                    (store_id, product_id),
                )
                result = cursor.fetchone()
                if not result:
                    cursor.close()
                    return error.error_non_exist_book_id(product_id) + (order_id,)

                current_stock = result[1]
                book_info = json.loads(result[2])
                unit_price = book_info.get("price")
                total_amount += unit_price * quantity

                # 检查库存是否足够
                if current_stock < quantity:
                    cursor.close()
                    return error.error_stock_level_low(product_id) + (order_id,)

                # 更新库存
                cursor.execute(
                    "UPDATE store SET stock_level = stock_level - %s "
                    "WHERE store_id = %s AND book_id = %s AND stock_level >= %s;",
                    (quantity, store_id, product_id, quantity),
                )
                if cursor.rowcount == 0:
                    cursor.close()
                    return error.error_stock_level_low(product_id) + (order_id,)

                # 插入订单详情
                cursor.execute(
                    "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                    "VALUES(%s, %s, %s, %s);",
                    (new_order_id, product_id, quantity, unit_price),
                )

            # 更新订单总金额
            cursor.execute(
                "UPDATE new_order SET total_price = %s WHERE order_id = %s;",
                (total_amount, new_order_id),
            )
            # 提交事务
            self.conn.commit()

            order_id = new_order_id
            cursor.close()
        except psycopg2.Error as db_error:
            logging.error(f"528, {str(db_error)}")
            self.conn.rollback()
            return 528, f"{str(db_error)}", ""
        except Exception as ex:
            logging.error(f"530, {str(ex)}")
            self.conn.rollback()
            return 530, f"{str(ex)}", ""

        return 200, "ok", order_id

    def process_payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            cursor = self.conn.cursor()
            # 查询订单是否存在
            cursor.execute(
                "SELECT order_id, user_id, store_id FROM new_order WHERE order_id = %s;",
                (order_id,),
            )
            order = cursor.fetchone()
            if not order:
                cursor.close()
                return error.error_invalid_order_id(order_id)

            retrieved_order_id, buyer_id, store_id = order

            # 验证买家身份
            if buyer_id != user_id:
                cursor.close()
                return error.error_authorization_fail()

            # 查询用户的账户信息
            cursor.execute(
                "SELECT balance, password FROM users WHERE user_id = %s;", (buyer_id,)
            )
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return error.error_non_exist_user_id(buyer_id)

            user_balance, stored_password = user
            if password != stored_password:
                cursor.close()
                return error.error_authorization_fail()

            # 查询商店信息
            cursor.execute(
                "SELECT store_id, user_id FROM user_store WHERE store_id = %s;",
                (store_id,),
            )
            store = cursor.fetchone()
            if not store:
                cursor.close()
                return error.error_non_exist_store_id(store_id)

            seller_id = store[1]

            # 验证商店卖家身份
            if not self._verify_user(seller_id):
                cursor.close()
                return error.error_non_exist_user_id(seller_id)

            # 获取订单金额
            cursor.execute(
                "SELECT total_price FROM new_order WHERE order_id = %s;",
                (order_id,),
            )
            price_row = cursor.fetchone()
            total_price = int(price_row[0])

            # 检查余额是否足够
            if user_balance < total_price:
                cursor.close()
                return error.error_not_sufficient_funds(order_id)

            # 开始转账事务
            cursor.execute(
                "UPDATE users SET balance = balance - %s "
                "WHERE user_id = %s AND balance >= %s;",
                (total_price, buyer_id, total_price),
            )
            if cursor.rowcount == 0:
                cursor.close()
                return error.error_not_sufficient_funds(order_id)

            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s;",
                (total_price, seller_id),
            )
            if cursor.rowcount == 0:
                cursor.close()
                return error.error_non_exist_user_id(seller_id)

            # 更新订单状态为“待发货”
            cursor.execute(
                "UPDATE new_order SET status = %s WHERE order_id = %s;",
                ("pending", order_id),
            )

            self.conn.commit()
            cursor.close()

        except psycopg2.Error as db_error:
            logging.error(f"528, {str(db_error)}")
            self.conn.rollback()
            return 528, f"{str(db_error)}"

        except Exception as ex:
            logging.error(f"530, {str(ex)}")
            self.conn.rollback()
            return 530, f"{str(ex)}"

        return 200, "ok"

    def deposit_funds(self, user_id, password, amount) -> (int, str):
        try:
            cursor = self.conn.cursor()
            # 查询用户密码是否正确
            cursor.execute(
                "SELECT password FROM users WHERE user_id = %s;", (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return error.error_authorization_fail()

            stored_password = user[0]
            if stored_password != password:
                cursor.close()
                return error.error_authorization_fail()

            # 更新用户余额
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s;",
                (amount, user_id),
            )
            if cursor.rowcount == 0:
                cursor.close()
                return error.error_non_exist_user_id(user_id)

            self.conn.commit()
            cursor.close()
        except psycopg2.Error as db_error:
            logging.error(f"528, {str(db_error)}")
            self.conn.rollback()
            return 528, f"{str(db_error)}"
        except Exception as ex:
            logging.error(f"530, {str(ex)}")
            self.conn.rollback()
            return 530, f"{str(ex)}"

        return 200, "ok"

    def acknowledge_receipt(self, user_id: str, order_id: str) -> (int, str):
        """
        买家确认收货
        """
        try:
            # 验证用户是否存在
            if not self._verify_user(user_id):
                return error.error_non_exist_user_id(user_id)

            cursor = self.conn.cursor()
            # 验证订单是否存在
            cursor.execute(
                "SELECT order_id FROM new_order WHERE order_id = %s;", (order_id,)
            )
            if not cursor.fetchone():
                cursor.close()
                return error.error_invalid_order_id(order_id)

            # 更新订单状态为“已完成”
            cursor.execute(
                "UPDATE new_order SET status = %s WHERE order_id = %s;",
                ("completed", order_id),
            )
            self.conn.commit()
            cursor.close()
        except psycopg2.Error as db_error:
            logging.error(f"528, {str(db_error)}")
            self.conn.rollback()
            return 528, f"Database error: {str(db_error)}"
        return 200, "ok"

    def cancel_user_order(self, user_id: str, order_id: str) -> (int, str):
        """
        取消订单
        """
        try:
            # 验证用户是否存在
            if not self._verify_user(user_id):
                return error.error_non_exist_user_id(user_id)

            cursor = self.conn.cursor()
            # 检查订单状态是否为“待发货”或“未支付”
            cursor.execute(
                "SELECT status FROM new_order WHERE order_id = %s;",
                (order_id,),
            )
            status = cursor.fetchone()
            if not status:
                cursor.close()
                return error.error_invalid_order_id(order_id)
            current_status = status[0]
            if current_status not in ["pending", "unpaid"]:
                cursor.close()
                return 400, "Order cannot be cancelled"

            # 删除订单详情和订单
            cursor.execute(
                "DELETE FROM new_order_detail WHERE order_id = %s;", (order_id,)
            )
            cursor.execute(
                "DELETE FROM new_order WHERE order_id = %s;", (order_id,)
            )

            self.conn.commit()
            cursor.close()
        except psycopg2.Error as db_error:
            logging.error(f"528, {str(db_error)}")
            self.conn.rollback()
            return 528, f"{str(db_error)}"
