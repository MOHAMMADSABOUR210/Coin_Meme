from django.urls import path
from . import views
from .views import deposit, transfer, TransactionListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [   
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('wallet/deposit/', deposit, name='deposit'),
    path('wallet/transfer/', transfer, name='transfer'),
    path('wallet/transactions/', TransactionListView.as_view(), name='transactions'),
]
