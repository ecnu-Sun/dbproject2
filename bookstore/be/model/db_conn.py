from be.model import store

class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    def user_id_exist(self, user_id):
        with self.conn.cursor() as cursor:  # 使用 with 语句确保 cursor 自动关闭
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s;", (user_id,)  # 修改: 使用 %s 作为占位符
            )
            return cursor.fetchone() is not None

    def book_id_exist(self, store_id, book_id):
        with self.conn.cursor() as cursor:  # 使用 with 语句
            cursor.execute(
                "SELECT book_id FROM store WHERE store_id = %s AND book_id = %s;",
                (store_id, book_id),  # 保持原来的查询逻辑
            )
            return cursor.fetchone() is not None

    def store_id_exist(self, store_id):
        with self.conn.cursor() as cursor:  # 使用 with 语句
            cursor.execute(
                "SELECT store_id FROM user_store WHERE store_id = %s;", (store_id,)  # 使用 %s 作为占位符
            )
            return cursor.fetchone() is not None
