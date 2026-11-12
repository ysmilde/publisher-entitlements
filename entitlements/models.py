from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    """
    Custom user model that extends the default Django AbstractUser.
    Additional fields can be added here as needed.
    Note: Admins have is_staff=True. They can log in and manage access. Regular users have is_staff=False. They’re the ones who hold subscriptions.
    """

class Benefit(models.Model):
    """
    Model representing a benefit that can be associated with products. It will be used to determine what a user has access to based on their subscriptions.
    """
    name = models.CharField(max_length=255, unique=True)
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
    Model representing a subscription that a user can have for a product. It is the relation between user and product.
    Note: did not add a unique constraint yet, will circle back if I have time
    """
    # if a user deletes their account, we will delete their subscriptions as well -- later on we can change this or add an audit trail to keep track of deleted users and their subscriptions
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    # do not delete a product if a subscription exists
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='subscriptions')
    granted_date = models.DateTimeField(auto_now_add=True)
    expire_date = models.DateTimeField(blank=True, null=True) # will compute is active by checking expire_date and is_revoked
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


