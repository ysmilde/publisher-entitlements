from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Benefit, Product, Subscription, User

admin.site.register(User, UserAdmin)
admin.site.register(Product)
admin.site.register(Benefit)
admin.site.register(Subscription)
