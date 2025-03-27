from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Категория")

    def __str__(self):
        return self.name

class Bouquet(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="bouquets", verbose_name="Категория")
    image_url = models.URLField(verbose_name="Ссылка на изображение")

    def __str__(self):
        return self.name

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    name = models.CharField(max_length=255, verbose_name="Имя пользователя")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменен')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bouquet = models.ForeignKey(Bouquet, on_delete=models.CASCADE, verbose_name="Букет")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итоговая цена")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заказ {self.id} - {self.user.name}"

class ConsultationRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата запроса")
    processed = models.BooleanField(default=False, verbose_name="Обработан")

    def __str__(self):
        return f"Запрос {self.id} от {self.user.name}"
