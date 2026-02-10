from django.db import models
from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')
        super().save(*args, **kwargs)