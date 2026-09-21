from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from accounts.models import CustomUser
from offers.models import CountdownOffer
from reviews.models import Review
from catalog.models import Category, DeliveryArea, Product

PASTEL = {
    "birthday": (255, 214, 165),
    "bento": (255, 183, 197),
    "cupcake": (208, 231, 200),
    "cookie": (222, 184, 135),
    "brownie": (160, 120, 90),
    "toppers": (196, 181, 253),
}


def _jpg(name, category):
    """Generate a simple placeholder cake image as a JPEG ContentFile."""
    color = PASTEL.get(category, (255, 224, 178))
    img = Image.new("RGB", (600, 600), color)
    d = ImageDraw.Draw(img)
    d.ellipse([180, 160, 420, 400], fill=(255, 255, 255))
    d.rectangle([210, 300, 390, 340], fill=(255, 255, 255))
    d.rectangle([210, 280, 390, 300], fill=(170, 60, 40))
    d.arc([180, 160, 420, 400], 190, 350, fill=(255, 255, 255), width=16)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return ContentFile(buf.getvalue(), name=f"{name}.jpg")


class Command(BaseCommand):
    help = "Seed the bakery API with sample categories, products, offers and a demo admin."

    def handle(self, *args, **options):
        if CustomUser.objects.filter(username="admin").exists():
            self.stdout.write("Admin user already exists, skipping user creation.")
        else:
            CustomUser.objects.create_superuser(
                username="admin", email="admin@sweettreats.local", password="admin12345"
            )
            self.stdout.write(self.style.SUCCESS("Superuser created (admin / admin12345)"))

        categories_data = [
            ("Birthday Cakes", "Cakes for every age and milestone", "birthday", 1),
            ("Bento Cakes", "Personal mini cakes in a box — perfect for small celebrations", "bento", 2),
            ("Cupcakes", "Cupcakes in every flavour you can dream of", "cupcake", 3),
            ("Cookies", "Crunchy, chewy, and oh-so-sweet cookies", "cookie", 4),
            ("Brownies", "Fudgy, gooey brownies baked to perfection", "brownie", 5),
            ("Cake Toppers & Decorations", "Edible toppers and decorations to make it your own", "toppers", 6),
        ]

        categories = {}
        for name, desc, key, order in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={"description": desc, "sort_order": order, "image": _jpg(name, key)},
            )
            categories[key] = cat
            self.stdout.write(f"  ✓ Category: {name}")

        if not DeliveryArea.objects.exists():
            DeliveryArea.objects.create(name="Downtown", delivery_fee=Decimal("40"), estimated_time="30-45 min")
            DeliveryArea.objects.create(name="Uptown", delivery_fee=Decimal("60"), estimated_time="45-60 min")
            DeliveryArea.objects.create(name="Suburbs", delivery_fee=Decimal("90"), estimated_time="60-90 min")
            DeliveryArea.objects.create(name="Nearby City", delivery_fee=Decimal("120"), estimated_time="1-2 hours")
            self.stdout.write("  ✓ Delivery areas created")

        products_data = [
            ("birthday", "Classic Chocolate Birthday Cake", "Rich, moist chocolate sponge with silky chocolate ganache. Perfect for any celebration.", "1999", True, True),
            ("birthday", "Strawberry Cream Cake", "Vanilla sponge layered with fresh strawberries and whipped cream.", "1799", False, True),
            ("bento", "Bento Cake Box — Mini Delight", "A personal 1-slice cake in a cute presentation box. Great for small surprises.", "549", False, True),
            ("bento", "Bento Letter Cake", "Letter-themed mini cake that spells out your message.", "649", True, True),
            ("cupcake", "Classic Vanilla Cupcake (Box of 6)", "Six fluffy vanilla cupcakes topped with swirls of buttercream.", "799", False, True),
            ("cupcake", "Red Velvet Cupcake (Box of 6)", "Six red velvet cupcakes with cream cheese frosting.", "899", False, True),
            ("cookie", "Chocolate Chip Cookies (Pack of 12)", "Baked with generous chunks of Belgian chocolate.", "799", False, True),
            ("cookie", "Goodie Box — Assorted Cookies", "A mixed box of our most-loved cookies. Great for gifting.", "999", False, True),
            ("brownie", "Fudgy Walnut Brownie Slab", "Gooey, chocolatey brownie slab topped with crunchy walnuts.", "799", False, True),
            ("brownie", "S'mores Brownie Box", "Brownies topped with marshmallows and graham crumbs.", "899", False, True),
            ("toppers", "Custom Name Cake Topper", "Personalised acrylic name topper, available in multiple colours.", "499", True, True),
            ("toppers", "Edible Photo Topper", "Edible printed topper using your own photo or logo.", "349", True, True),
        ]

        products = {}
        for cat_key, name, desc, price, customizable, featured in products_data:
            cat = categories[cat_key]
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": cat,
                    "description": desc,
                    "base_price": Decimal(price),
                    "image": _jpg(name.lower().replace(" ", "_").replace("—", "_"), cat_key),
                    "is_customizable": customizable,
                    "is_featured": featured,
                    "is_available": True,
                    "stock": 10,
                    "sizes": ["small", "medium", "large"] if "cake" in name.lower() else [],
                    "flavors": ["vanilla", "chocolate", "strawberry"] if "cake" in name.lower() else ["vanilla", "chocolate"],
                },
            )
            products[name] = product
            self.stdout.write(f"  ✓ Product: {name}")

        sale_product = Product.objects.filter(name__icontains="Bento Letter").first()
        if sale_product and not sale_product.sale_price:
            sale_product.sale_price = sale_product.base_price - Decimal("150")
            sale_product.save()
            self.stdout.write("  ✓ Applied sale price to Bento Letter Cake")

        demo_user, _ = CustomUser.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@sweettreats.local",
                "first_name": "Demo",
                "last_name": "User",
                "phone": "555-1234",
                "password": "",
            },
        )
        demo_user.set_password("demo12345")
        demo_user.save()

        if not Review.objects.exists():
            for product in list(products.values())[:6]:
                Review.objects.create(
                    product=product,
                    user=demo_user,
                    rating=5,
                    title="Absolutely delicious!",
                    comment="Ordered for a birthday and they loved it. Fresh, beautiful and so tasty. Will order again!",
                )
            self.stdout.write("  ✓ Sample reviews created")

        now = timezone.now()
        offer, created = CountdownOffer.objects.get_or_create(
            slug="weekend-baking-sale",
            defaults={
                "name": "Weekend Baking Sale",
                "discount_percent": 15,
                "banner_message": "Weekend flash sale on our bestsellers",
                "starts_at": now - timezone.timedelta(hours=1),
                "ends_at": now + timezone.timedelta(hours=72),
                "is_active": True,
            },
        )
        if created:
            offer.products.set(list(products.values())[:6])
            self.stdout.write("  ✓ Countdown offer created (72h)")

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Run 'python manage.py runserver 0.0.0.0:8000' — admin/admin12345 for the admin panel."
            )
        )