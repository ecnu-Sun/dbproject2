import os
import psycopg2
import random
import base64
import simplejson as json


class BookDetails:
    book_id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    publication_year: str
    page_count: int
    price_in_cents: int
    currency: str
    binding_type: str
    isbn_code: str
    author_description: str
    book_summary: str
    content_description: str
    genre_tags: [str]
    images: [bytes]

    def __init__(self):
        self.genre_tags = []
        self.images = []


class BookDatabase:
    def __init__(self, use_large: bool):
        self.connection = psycopg2.connect(
            dbname="bookstore", user="postgres", password="Qq132465321", host="127.0.0.1", port="5432"
        )

    def get_total_book_count(self):
        """
        获取 books 表中的总记录数
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT count(id) FROM books")
        result = cursor.fetchone()
        cursor.close()
        return result[0]

    def fetch_books(self, offset: int, limit: int) -> [BookDetails]:
        """
        获取 books 表中的书籍信息
        :param offset: 起始记录位置
        :param limit: 获取的书籍数量
        :return: 书籍对象列表
        """
        books_list = []
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, title, author, 
                publisher, original_title, 
                translator, pub_year, pages, 
                price, currency_unit, binding, 
                isbn, author_intro, book_intro, 
                content, tags, picture 
            FROM books 
            ORDER BY id 
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        for record in cursor:
            book = BookDetails()
            book.book_id = record[0]
            book.title = record[1]
            book.author = record[2]
            book.publisher = record[3]
            book.original_title = record[4]
            book.translator = record[5]
            book.publication_year = record[6]
            book.page_count = record[7]
            book.price_in_cents = record[8]

            book.currency = record[9]
            book.binding_type = record[10]
            book.isbn_code = record[11]
            book.author_description = record[12]
            book.book_summary = record[13]
            book.content_description = record[14]
            genre_tags = record[15]

            image_data = record[16]

            # 处理标签
            for tag in genre_tags.split("\n"):
                if tag.strip() != "":
                    book.genre_tags.append(tag)

            # 处理图片
            for _ in range(0, random.randint(0, 9)):
                if image_data is not None:
                    encoded_image = base64.b64encode(image_data).decode("utf-8")
                    book.images.append(encoded_image)

            books_list.append(book)

        cursor.close()
        return books_list
