from flask import Blueprint, request, jsonify
from be.model import buyer as buyer_model

buyer_bp = Blueprint("buyer", __name__, url_prefix="/buyer")


@buyer_bp.route("/new_order", methods=["POST"])
def create_new_order():
    user_id = request.json.get("user_id")
    store_id = request.json.get("store_id")
    books = request.json.get("books")

    order_items = [(book.get("id"), book.get("count")) for book in books]

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg, order_id = buyer_instance.new_order(user_id, store_id, order_items)

    return jsonify({"message": response_msg, "order_id": order_id}), status_code


@buyer_bp.route("/payment", methods=["POST"])
def process_payment():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    password = request.json.get("password")

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg = buyer_instance.payment(user_id, password, order_id)

    return jsonify({"message": response_msg}), status_code


@buyer_bp.route("/add_funds", methods=["POST"])
def fund_account():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    amount_to_add = request.json.get("add_value")

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg = buyer_instance.add_funds(user_id, password, amount_to_add)

    return jsonify({"message": response_msg}), status_code


@buyer_bp.route("/confirm_receipt", methods=["POST"])
def confirm_order_receipt():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg = buyer_instance.confirm_receipt(user_id, order_id)

    return jsonify({"message": response_msg}), status_code


@buyer_bp.route("/query_orders", methods=["GET"])
def retrieve_orders():
    user_id = request.args.get("user_id")

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg, orders = buyer_instance.query_orders(user_id)

    if status_code == 200:
        return jsonify({"message": response_msg, "orders": orders}), status_code
    else:
        return jsonify({"message": response_msg}), status_code


@buyer_bp.route("/cancel_order", methods=["POST"])
def cancel_existing_order():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")

    buyer_instance = buyer_model.Buyer()
    status_code, response_msg = buyer_instance.cancel_order(user_id, order_id)

    return jsonify({"message": response_msg}), status_code
