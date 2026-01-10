"""
Caller Model - Stores caller personal information
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class Caller(Model):
    id = fields.IntField(pk=True)
    full_name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    phone = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "callers"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

