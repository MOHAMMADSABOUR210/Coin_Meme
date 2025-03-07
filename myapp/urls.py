from django.urls import path
from . import views
from .views import transfer, TransactionListView,StatisticsView,WalletAddressView,CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [   
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('wallet/transfer/', transfer, name='transfer'),
    path('wallet/transactions/', TransactionListView.as_view(), name='transactions'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('wallet/address/', WalletAddressView.as_view(), name='wallet-address'),
    path('wallet/deposit/', views.deposit, name='deposit'),
    path('wallet/balance/', views.check_balance, name='check_balance'),

]
