from django.urls import path
from . import views
from .views import transfer, TransactionListView,StatisticsView,WalletAddressView,CustomTokenObtainPairView ,SendMessageView, ChatListView, ChatMessagesView,SendFileView
from rest_framework_simplejwt.views import TokenRefreshView
from myapp.views import ExportTransactionsCSVView


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
    path('wallet/export/csv/', ExportTransactionsCSVView.as_view(), name='export_transactions_csv'),
    path('messages/send/', SendMessageView.as_view(), name='send_message'),
    path('messages/send-file/<str:wallet_address>/', SendFileView.as_view(), name='send_file'), 
    path('messages/chats/', ChatListView.as_view(), name='chat_list'),
    path('messages/chat/<str:wallet_address>/', ChatMessagesView.as_view(), name='chat_messages'),
]
