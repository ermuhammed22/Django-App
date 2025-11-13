from csv import DictReader
from io import TextIOWrapper
from django.contrib.auth.models import User
from shopapp.models import Product, Order


def save_csv_products(file, encoding,request):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    reader = DictReader(csv_file)

    products_to_create = []
    for row in reader:
        created_by_user = None
        if request.user.is_authenticated:
            created_by_user = request.user

        product = Product(
            name=row["name"],
            description=row["description"],
            price=float(row["price"]),
            discount=int(row["discount"]),
            created_by=created_by_user
        )
        products_to_create.append(product)

    Product.objects.bulk_create(products_to_create)
    return products_to_create


def save_csv_orders(file, encoding):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    reader = DictReader(csv_file)

    orders_created = 0
    for row in reader:
        try:
            user = User.objects.get(pk=row["user_id"])
            order = Order.objects.create(
                user=user,
                delivery_address=row["delivery_address"],
                promocode=row["promocode"]
            )

            product_pks = row["product_ids"].split(',')
            products = Product.objects.filter(pk__in=product_pks)
            order.products.set(products)
            orders_created += 1

        except Exception as e:
            print(f"Ошибка импорта заказа: {e} для строки: {row}")
            pass

    return orders_created