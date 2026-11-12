from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    """
    Custom user model that extends the default Django AbstractUser.
    Additional fields can be added here as needed.
    """

class Benefit(models.Model):
    """
    Model representing a benefit that can be associated with products. It will be used to determine what a user has access to based on their subscriptions.
    """
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Model representing a product in the system. E.g. digital, print, premium
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    benefits = models.ManyToManyField(Benefit, related_name='products', blank=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    """
    Model representing the relationship between user and product.
    This will be auditable, meaning we can keep track of a user's subscription history. 
    A user can have multiple subscriptions for the same product over time, but only one active subscription at a time.
    Note: need to add a unique constraint to ensure a user can only have one active subscription for a product at a 
    time will circle back to this later. For now, we will handle this in the service layer.
    """
    # if a user deletes their account, we will delete their subscriptions as well -- later on we can change this or add an audit trail to keep track of deleted users and their subscriptions
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    # do not delete a product if a subscription exists
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='subscriptions')
    granted_date = models.DateTimeField(auto_now_add=True)
    expire_date = models.DateTimeField() # will compute is active by checking expire_date and revoked_at
    revoked_at = models.DateTimeField(blank=True, null=True) # null = not revoked

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


