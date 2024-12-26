import logging
import psycopg2
import threading
from psycopg2 import extensions


class Store:
    def __init__(self):
        """
        初始化数据库连接配置，直接连接到 PostgreSQL 数据库
        """
        # 硬编码 PostgreSQL 数据库连接信息
        self.dbname = 'bookstore'  # 数据库名
        self.user = 'postgres'  # 数据库用户
        self.password = 'Qq132465321'  # 数据库密码
        self.host = 'localhost'  # 数据库主机地址
        self.port = '5432'  # 数据库端口

        try:
            # 初始化数据库连接
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            # 设置事务隔离级别为 SERIALIZABLE
            self.conn.set_isolation_level(extensions.ISOLATION_LEVEL_SERIALIZABLE)
            self.init_tables()  # 初始化表结构
        except psycopg2.Error as e:
            logging.error(f"Failed to connect to the database: {e}")
            raise

    def init_tables(self):
        """
        初始化数据库表
        """
        try:
            if self.conn.closed:
                logging.error("Database connection is closed. Unable to execute SQL.")
                raise psycopg2.OperationalError("Database connection is not open.")

            # 按顺序创建表
            table_statements = [
                """
                CREATE TABLE IF NOT EXISTS users(
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    balance INT NOT NULL,
                    token TEXT,
                    terminal TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS user_store(
                    user_id TEXT,
                    store_id TEXT PRIMARY KEY,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS store(
                    store_id TEXT,
                    book_id TEXT,
                    book_info TEXT,
                    stock_level INT,
                    PRIMARY KEY (store_id, book_id),
                    FOREIGN KEY (store_id) REFERENCES user_store(store_id),
                    FOREIGN KEY (book_id) REFERENCES books(id)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS new_order(
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    store_id TEXT, 
                    status TEXT,
                    total_price INT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (store_id) REFERENCES user_store(store_id)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS new_order_detail(
                    order_id TEXT,
                    book_id TEXT,
                    count INT,
                    price INT,
                    PRIMARY KEY (order_id, book_id),
                    FOREIGN KEY (order_id) REFERENCES new_order(order_id),
                    FOREIGN KEY (book_id) REFERENCES books(id)
                );
                """
            ]

            with self.conn.cursor() as cursor:  # 使用 with 语句来管理 cursor
                for statement in table_statements:
                    cursor.execute(statement)
                self.conn.commit()
        except psycopg2.Error as e:
            logging.error(f"Database error during table initialization: {e}")
            if self.conn:
                self.conn.rollback()

    def get_db_conn(self):
        """
        获取数据库连接，如果连接已关闭则重新连接
        """
        try:
            if self.conn.closed:  # psycopg2.Connection.closed 返回 0 表示连接打开
                logging.warning("Database connection was closed. Reconnecting...")
                self.conn = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
        except psycopg2.Error as e:
            logging.error(f"Error reconnecting to the database: {e}")
            raise
        return self.conn


# 全局数据库实例和同步事件
database_instance: Store = None
init_completed_event = threading.Event()


def init_database():
    """
    初始化数据库实例
    """
    global database_instance
    database_instance = Store()
    init_completed_event.set()


def get_db_conn():
    """
    获取全局数据库连接
    """
    global database_instance
    return database_instance.get_db_conn()
