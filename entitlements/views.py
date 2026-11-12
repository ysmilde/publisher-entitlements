from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import grant_product, revoke_product, get_user_entitlements
from .models import Benefit, Product
from .serializers import BenefitSerializer, SubscriptionSerializer, UserProductSerializer

class GrantProductView(APIView):
    """
    API endpoint to grant a product to a user.
    """
    def post(self, request):
        serializer = UserProductSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            product_id = serializer.validated_data['product_id']
            try:
                user = get_object_or_404(get_user_model(), id=user_id)
                product = get_object_or_404(Product, id=product_id)
                subscription = grant_product(user, product)
                return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RevokeProductView(APIView):
    """
    API endpoint to revoke a product from a user.
    """
    def post(self, request):
        serializer = UserProductSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            product_id = serializer.validated_data['product_id']
            try:
                user = get_object_or_404(get_user_model(), id=user_id)
                product = get_object_or_404(Product, id=product_id)
                subscription = revoke_product(user, product)
                return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserEntitlementsView(APIView):
    """
    API endpoint to retrieve a user's entitlements (benefits) based on their active subscriptions.
    """
    def get(self, request, user_id):
        user = get_object_or_404(get_user_model(), id=user_id)
        benefits = get_user_entitlements(user)
        return Response([BenefitSerializer(benefit).data for benefit in benefits], status=status.HTTP_200_OK)
