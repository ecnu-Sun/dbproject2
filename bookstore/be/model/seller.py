import psycopg2
from be.model import error
from psycopg2 import errors
from be.model import db_conn
import logging

class Seller(db_conn.DBConn):
    def __init__(self):
        super().__init__()  # 使用 super() 简化继承调用

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            with self.conn.cursor() as cursor:  # 使用 with 语句管理 cursor
                cursor.execute(
                    "INSERT INTO store(store_id, book_id, book_info, stock_level) "
                    "VALUES (%s, %s, %s, %s);",
                    (store_id, book_id, book_json_str, stock_level),
                )
                self.conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Database error in add_book: {str(e)}")
            self.conn.rollback()
            return 528, f"{str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in add_book: {str(e)}")
            self.conn.rollback()
            return 530, f"{str(e)}"
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            with self.conn.cursor() as cursor:  # 使用 with 语句
                cursor.execute(
                    "UPDATE store SET stock_level = stock_level + %s "
                    "WHERE store_id = %s AND book_id = %s;",
                    (add_stock_level, store_id, book_id),
                )
                self.conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Database error in add_stock_level: {str(e)}")
            self.conn.rollback()
            return 528, f"{str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in add_stock_level: {str(e)}")
            self.conn.rollback()
            return 530, f"{str(e)}"
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_store(store_id, user_id) VALUES (%s, %s);",
                    (store_id, user_id),
                )
                self.conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Database error in create_store: {str(e)}")
            self.conn.rollback()
            return 528, f"{str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error in create_store: {str(e)}")
            self.conn.rollback()
            return 530, f"{str(e)}"
        return 200, "ok"

    def confirm_shipping(self, user_id: str, order_id: str) -> (int, str):
        """
        卖家确认发货
        """
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            with self.conn.cursor() as cursor:  # 使用 with 语句
                # 检查订单是否存在
                cursor.execute(
                    "SELECT order_id FROM new_order WHERE order_id = %s;", (order_id,)
                )
                if cursor.fetchone() is None:
                    return error.error_invalid_order_id(order_id)

                # 更新订单状态为“已发货”
                cursor.execute(
                    "UPDATE new_order SET status = %s WHERE order_id = %s;",
                    ("shipped", order_id),
                )
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            logging.error(f"Database error in confirm_shipping: {str(e)}")
            return 528, f"Database error: {str(e)}"
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Unexpected error in confirm_shipping: {str(e)}")
            return 530, f"{str(e)}"
        return 200, "ok"
