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
    