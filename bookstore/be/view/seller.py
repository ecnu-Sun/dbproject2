from flask import Blueprint, request, jsonify
from be.model import seller as seller_model
import json

seller_bp = Blueprint("seller", __name__, url_prefix="/seller")

@seller_bp.route("/create_store", methods=["POST"])
def initialize_store():
    user_id = request.json.get("user_id")
    store_id = request.json.get("store_id")
    seller_instance = seller_model.Seller()
    status_code, response_msg = seller_instance.create_store(user_id, store_id)
    return jsonify({"message": response_msg}), status_code

@seller_bp.route("/add_book", methods=["POST"])
def add_new_book():
    user_id = request.json.get("user_id")
    store_id = request.json.get("store_id")
    book_details = request.json.get("book_info")
    stock_quantity = request.json.get("stock_level", 0)

    seller_instance = seller_model.Seller()
    status_code, response_msg = seller_instance.add_book(
        user_id, store_id, book_details.get("id"), json.dumps(book_details), stock_quantity
    )

    return jsonify({"message": response_msg}), status_code

@seller_bp.route("/add_stock_level", methods=["POST"])
def update_stock_level():
    user_id = request.json.get("user_id")
    store_id = request.json.get("store_id")
    book_id = request.json.get("book_id")
    additional_stock = request.json.get("add_stock_level", 0)

    seller_instance = seller_model.Seller()
    status_code, response_msg = seller_instance.add_stock_level(user_id, store_id, book_id, additional_stock)

    return jsonify({"message": response_msg}), status_code

@seller_bp.route("/confirm_shipping", methods=["POST"])
def confirm_shipment():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")

    seller_instance = seller_model.Seller()
    status_code, response_msg = seller_instance.confirm_shipping(user_id, order_id)

    return jsonify({"message": response_msg}), status_code
