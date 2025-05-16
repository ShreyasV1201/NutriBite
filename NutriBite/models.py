# NutriBite/models.py
from django.db import models
from django.conf import settings

class FavoriteRecipe(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fdc_id     = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    mealdb_id  = models.CharField(max_length=32, blank=True, null=True)
    title      = models.CharField(max_length=255)
    image      = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            ("user", "fdc_id"),
            ("user", "mealdb_id"),
        )

class Recipe(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes",)
    title        = models.CharField(max_length=200)
    ingredients  = models.TextField(help_text="List one ingredient per line")
    preparation  = models.TextField()
