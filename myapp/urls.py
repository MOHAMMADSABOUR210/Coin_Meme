from django.urls import path
from . import views
from .views import deposit, transfer, TransactionListView


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('wallet/deposit/', deposit, name='deposit'),
    path('wallet/transfer/', transfer, name='transfer'),
    path('wallet/transactions/', TransactionListView.as_view(), name='transactions'),
]
