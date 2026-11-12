from rest_framework import serializers

from .models import Benefit, Product, Subscription

# Output serializers

class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefit
        fields = ['id', 'name', 'code', 'description']

class ProductSerializer(serializers.ModelSerializer):
    """ 
    Serializer for the Product model, including its associated benefits.
    """
    benefits = BenefitSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'created_at', 'updated_at', 'benefits']

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Subscription model, including its associated product.
    """
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'product', 'granted_date', 'expire_date', 'revoked_at']

# Input serializers

class UserProductSerializer(serializers.Serializer):
    """
    Serializer for granting and revoking a product from a user.
    """
    product_id = serializers.IntegerField(min_value=1)
    user_id = serializers.IntegerField(min_value=1)