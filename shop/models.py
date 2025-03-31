from django.db import models


class Bouquet(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    photo = models.ImageField(upload_to='bouquets/', blank=True, null=True)
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
    bouquet = models.ForeignKey(Bouquet, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.IntegerField()
    address = models.TextField()
    delivery_date = models.CharField(max_length=50)
    delivery_time = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Заказ от {self.created_at.strftime("%d.%m.%Y %H:%M")} — {self.price} руб.'


class ConsultationRequest(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    occasion = models.CharField(max_length=100, blank=True, null=True)
    budget = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Консультация от {self.name} — {self.phone}'
