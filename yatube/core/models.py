from django.db import models


class CreatedModel(models.Model):
    """Basic model."""
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True
