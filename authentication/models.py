import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from payment_api.utils import generate_api_key


class MerchantManager(BaseUserManager):
    """Custom manager for Merchant model"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular merchant"""
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        merchant = self.model(email=email, **extra_fields)
        merchant.set_password(password)
        merchant.save(using=self._db)
        return merchant

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser merchant"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Merchant(AbstractBaseUser, PermissionsMixin):
    """Custom user model for merchants"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    api_key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MerchantManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'merchants'
        verbose_name = 'Merchant'
        verbose_name_plural = 'Merchants'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Generate API key on creation"""
        if not self.api_key:
            self.api_key = generate_api_key(settings.API_KEY_LENGTH)
        super().save(*args, **kwargs)
