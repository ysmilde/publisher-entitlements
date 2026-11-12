from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GrantProductView, RevokeProductView, UserEntitlementsView

router = DefaultRouter()

urlpatterns = router.urls + [
    path('subscriptions/', GrantProductView.as_view(), name='grant-product'),
    path('subscriptions/revoke/', RevokeProductView.as_view(), name='revoke-product'),
    path('users/<int:user_id>/entitlements/', UserEntitlementsView.as_view(), name='user-entitlements'),
]
