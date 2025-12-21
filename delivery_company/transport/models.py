from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('водитель', 'Водитель'),
        ('клиент', 'Клиент'),
        ('администратор', 'Администратор'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Добавляем новые поля
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)

    phone = models.CharField(max_length=20)

    class Meta:
        db_table = 'clients'

    def __str__(self):
        return f"Клиент: {self.last_name} {self.first_name}"


class Fleet(models.Model):
    STATUS_CHOICES = [
        ('используется', 'Используется'),  # Было "в эксплуатации"
        ('на стоянке', 'На стоянке'),  # Было "простой"
    ]

    license_plate = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='на стоянке')  # Добавил дефолт
    capacity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fleet'

    def __str__(self):
        return f"{self.model} ({self.license_plate})"


class Driver(models.Model):
    STATUS_CHOICES = [
        ('свободен', 'Свободен'),
        ('в пути', 'В пути'),
        ('на простое', 'На простое'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    driving_license = models.CharField(max_length=50)
    experience_years = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    fleet = models.ForeignKey(Fleet, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'drivers'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Cargo(models.Model):
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'cargos'

    def __str__(self):
        return f"{self.name} ({self.weight} кг)"


class Delivery(models.Model):
    STATUS_CHOICES = [
        ('оформлен', 'Оформлен'),
        ('в пути', 'В пути'),
        ('доставлен', 'Доставлен'),
        ('отменён', 'Отменён'),
    ]

    DELIVERY_TYPE_CHOICES = [
        ('локальная', 'Локальная'),
        ('междугородняя', 'Междугородняя'),
    ]

    client = models.ForeignKey(Client, on_delete=models.RESTRICT)
    cargo = models.ForeignKey(Cargo, on_delete=models.RESTRICT)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    delivery_type = models.CharField(max_length=50, choices=DELIVERY_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery'

    def __str__(self):
        return f"Доставка #{self.id} - {self.status}"

    def get_price(self):
        distance = self.route.distance if hasattr(self, 'route') and self.route.distance else 0
        weight = self.cargo.weight if self.cargo else 0

        # Преобразуем в Decimal для точных расчетов
        dist_dec = Decimal(str(distance))
        weight_dec = Decimal(str(weight))

        # Формула: 50 руб/км + 10 руб/кг
        price = (dist_dec * Decimal('50.00')) + (weight_dec * Decimal('10.00'))

        # Минимум 500 руб
        if price < 500:
            return Decimal('500.00')
        return price


class Route(models.Model):
    delivery = models.OneToOneField(Delivery, on_delete=models.RESTRICT)
    departure_city = models.CharField(max_length=100)
    departure_street = models.CharField(max_length=100)
    departure_house = models.CharField(max_length=20)
    arrival_city = models.CharField(max_length=100)
    arrival_street = models.CharField(max_length=100)
    arrival_house = models.CharField(max_length=20)
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'routes'

    def __str__(self):
        return f"Маршрут {self.departure_city} - {self.arrival_city}"


class Feedback(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.RESTRICT)
    client = models.ForeignKey(Client, on_delete=models.RESTRICT)
    submitted_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    class Meta:
        db_table = 'feedbacks'

    def __str__(self):
        return f"Отзыв от {self.client} по доставке #{self.delivery.id}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('карта', 'Карта'),
        ('наличные', 'Наличные'),
    ]

    delivery = models.ForeignKey(Delivery, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, choices=METHOD_CHOICES)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"Платёж {self.amount} - {self.status}"


class Refueling(models.Model):
    FUEL_TYPE_CHOICES = [
        ('АИ-92', 'АИ-92'),
        ('АИ-95', 'АИ-95'),
        ('ДТ', 'Дизель'),
        ('Газ', 'Газ'),
    ]

    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, verbose_name="Автомобиль")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Водитель")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заправки")
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, verbose_name="Вид топлива")
    liters = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Литры")
    cost_per_liter = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена за литр")
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Общая стоимость")

    class Meta:
        db_table = 'refueling'
        verbose_name = 'Заправка'
        verbose_name_plural = 'Заправки'

    def save(self, *args, **kwargs):
        # Автоматический расчет общей стоимости
        if self.liters and self.cost_per_liter:
            self.total_cost = self.liters * self.cost_per_liter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fleet.model} - {self.liters}л ({self.date.strftime('%d.%m.%Y')})"