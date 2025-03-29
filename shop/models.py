from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('florist', 'Флорист'),
        ('courier', 'Курьер'),
    ]

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    chat_id = models.BigIntegerField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['full_name', 'phone']

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return self.full_name or self.username


class Bouquet(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    photo = models.ImageField(upload_to='bouquets/')
    is_active = models.BooleanField(default=True)
    occasion = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['occasion']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменён'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    bouquet = models.ForeignKey(Bouquet, on_delete=models.PROTECT)

    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()
    delivery_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    courier = models.ForeignKey(User, related_name='deliveries', null=True, blank=True, on_delete=models.SET_NULL)
    florist = models.ForeignKey(User, related_name='handled_orders', null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['delivery_datetime']),
            models.Index(fields=['user']),
            models.Index(fields=['courier']),
            models.Index(fields=['florist']),
        ]

    def __str__(self):
        return f'Заказ #{self.pk}'
