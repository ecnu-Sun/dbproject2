import jwt
import time
import logging
import psycopg2
from psycopg2 import errors
from be.model import error
from be.model import db_conn


def jwt_encode(user_id: str, terminal: str) -> str:
    """生成 JWT 编码的 token"""
    return jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )


def jwt_decode(encoded_token: str, user_id: str) -> dict:
    """解码 JWT token"""
    return jwt.decode(encoded_token, key=user_id, algorithms="HS256")


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # Token 过期时间 3600秒

    def __init__(self):
        """初始化用户类，继承自 DBConn"""
        super().__init__()

    def _generate_terminal_and_token(self, user_id: str) -> (str, str):
        """生成 terminal 和 token"""
        terminal = f"terminal_{time.time()}"
        token = jwt_encode(user_id, terminal)
        return terminal, token

    def __check_token(self, user_id: str, db_token: str, token: str) -> bool:
        """检查 JWT token 是否有效"""
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text.get("timestamp")
            if ts is not None and self.token_lifetime > (time.time() - ts) >= 0:
                return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(f"Invalid token signature: {e}")
        return False

    def register(self, user_id: str, password: str) -> (int, str):
        """注册用户"""
        try:
            terminal, token = self._generate_terminal_and_token(user_id)
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users(user_id, password, balance, token, terminal) "
                    "VALUES (%s, %s, %s, %s, %s);",
                    (user_id, password, 0, token, terminal),
                )
                self.conn.commit()
        except errors.UniqueViolation:
            self.conn.rollback()
            return error.error_exist_user_id(user_id)
        except psycopg2.Error as e:
            self.conn.rollback()
            logging.error(f"Database error during user registration: {e}")
            return 528, "Database error"
        except Exception as e:
            logging.error(f"Unexpected error during registration: {e}")
            return 530, "Unexpected error"
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        """检查用户的 JWT token 是否有效"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT token FROM users WHERE user_id=%s;", (user_id,))
            row = cursor.fetchone()
        if row is None or not self.__check_token(user_id, row[0], token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        """检查用户的密码是否正确"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE user_id=%s;", (user_id,))
            row = cursor.fetchone()
        if row is None or password != row[0]:
            return error.error_authorization_fail()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        """用户登录，验证密码并生成 token"""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET token=%s, terminal=%s WHERE user_id=%s;",
                    (token, terminal, user_id),
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail() + ("",)
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            return 528, f"{e}", ""
        except BaseException as e:
            return 530, f"{e}", ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> (int, str):
        """用户登出，设置伪 token"""
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal, dummy_token = self._generate_terminal_and_token(user_id)
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET token=%s, terminal=%s WHERE user_id=%s;",
                    (dummy_token, terminal, user_id),
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail()
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            return 528, f"{e}"
        except BaseException as e:
            return 530, f"{e}"
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        """用户注销"""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE user_id=%s;", (user_id,))
                if cursor.rowcount == 1:
                    self.conn.commit()
                else:
                    return error.error_authorization_fail()
        except psycopg2.Error as e:
            self.conn.rollback()
            return 528, f"{e}"
        except BaseException as e:
            return 530, f"{e}"
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> (int, str):
        """用户修改密码"""
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal, token = self._generate_terminal_and_token(user_id)
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password=%s, token=%s, terminal=%s WHERE user_id=%s;",
                    (new_password, token, terminal, user_id),
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail()
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            return 528, f"{e}"
        except BaseException as e:
            return 530, f"{e}"
        return 200, "ok"
