from django.db import models
from django.contrib.auth.models import User


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


class VehicleMaintenance(models.Model):
    STATUS_CHOICES = [
        ('запланировано', 'Запланировано'),
        ('в процессе', 'В процессе'),
        ('завершено', 'Завершено'),
        ('отменено', 'Отменено'),
    ]

    fleet = models.ForeignKey(Fleet, on_delete=models.RESTRICT)
    service_date = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'vehicle_maintenance'

    def __str__(self):
        return f"ТО {self.fleet.license_plate} - {self.service_date}"


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