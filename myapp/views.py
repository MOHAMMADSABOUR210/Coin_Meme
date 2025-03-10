from django.contrib.auth import login, logout, authenticate
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LoginSerializer,ProfileSerializer ,ProfileEditSerializer,MessageSerializer, ChatListSerializer
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, Transaction, Message 
from decimal import Decimal
from .serializers import TransactionSerializer
from django.utils.dateparse import parse_date
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Sum
from django.contrib.auth.models import User
import uuid
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
import csv
from django.http import HttpResponse 
from django_filters.rest_framework import DjangoFilterBackend
from .filters import TransactionFilter
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from django.db.models import Q, Count, Max

@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful"})
        else:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)

    if not hasattr(user, 'wallet'):
        wallet = Wallet.objects.create(user=user, address=uuid.uuid4())  
        wallet.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "message": "User registered successfully.",
        "wallet_address": str(user.wallet.address),
        "access_token": access_token,
        "refresh_token": str(refresh),
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})

class ProfileEditView(APIView):
    def get(self, request):
        serializer = ProfileEditSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileEditSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile_edit(request):
    user = request.user
    serializer = ProfileSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    receiver_address = request.data.get('receiver_address')
    amount = request.data.get('amount')

    if not receiver_address or not amount:
        return Response({"error": "Receiver address and amount are required."}, status=status.HTTP_400_BAD_REQUEST)

    amount = Decimal(amount)
    sender_wallet = request.user.wallet

    if sender_wallet.balance < amount:
        return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        receiver_wallet = Wallet.objects.get(address=receiver_address)
    except Wallet.DoesNotExist:
        return Response({"error": "Receiver wallet not found."}, status=status.HTTP_404_NOT_FOUND)

    sender_wallet.balance -= amount
    receiver_wallet.balance += amount

    sender_wallet.save()
    receiver_wallet.save()

    Transaction.objects.create(
        wallet=sender_wallet,
        sender=sender_wallet,
        receiver=receiver_wallet,
        transaction_type='transfer',
        amount=amount
    )

    Transaction.objects.create(
        wallet=receiver_wallet,
        sender=sender_wallet,
        receiver=receiver_wallet,
        transaction_type='receive',
        amount=amount
    )

    return Response({"message": "Transfer successful."}, status=status.HTTP_200_OK)



class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(wallet=self.request.user.wallet)
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        min_amount = self.request.query_params.get("min_amount")
        max_amount = self.request.query_params.get("max_amount")
        username = self.request.query_params.get("username")

        if start_date:
            queryset = queryset.filter(timestamp__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(timestamp__lte=parse_date(end_date))
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        if username:
            queryset = queryset.filter(sender__user__username=username) | queryset.filter(receiver__user__username=username)

        return queryset


class WalletAddressView(APIView):
    permission_classes = [IsAuthenticated] 
    def get(self, request):
        try:
            wallet = Wallet.objects.get(user=request.user)
            return Response({"wallet_address": str(wallet.address)}, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transaction_count_week = Transaction.objects.filter(timestamp__gte='2025-03-01').count()
        transaction_count_month = Transaction.objects.filter(timestamp__gte='2025-02-01').count()
        transaction_count_year = Transaction.objects.filter(timestamp__gte='2024-03-01').count()

        transaction_volume_week = Transaction.objects.filter(timestamp__gte='2025-03-01').aggregate(Sum('amount'))
        transaction_volume_month = Transaction.objects.filter(timestamp__gte='2025-02-01').aggregate(Sum('amount'))
        transaction_volume_year = Transaction.objects.filter(timestamp__gte='2024-03-01').aggregate(Sum('amount'))

        message_count_week = Message.objects.filter(timestamp__gte='2025-03-01').count()
        message_count_month = Message.objects.filter(timestamp__gte='2025-02-01').count()
        message_count_year = Message.objects.filter(timestamp__gte='2024-03-01').count()

        statistics = {
            'transaction_count_week': transaction_count_week,
            'transaction_count_month': transaction_count_month,
            'transaction_count_year': transaction_count_year,
            'transaction_volume_week': transaction_volume_week['amount__sum'] or 0,
            'transaction_volume_month': transaction_volume_month['amount__sum'] or 0,
            'transaction_volume_year': transaction_volume_year['amount__sum'] or 0,
            'message_count_week': message_count_week,
            'message_count_month': message_count_month,
            'message_count_year': message_count_year,
        }

        return Response(statistics)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    amount = request.data.get('amount')

    if not amount or float(amount) <= 0:
        return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

    wallet = request.user.wallet
    amount = Decimal(amount)

    wallet.balance += amount
    wallet.save()
    Transaction.objects.create(
        wallet=wallet,
        transaction_type='deposit',
        amount=amount
    )

    return Response({"message": "Deposit successful.", "new_balance": wallet.balance}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def check_balance(request):
    user = request.user 

    try:
        wallet = Wallet.objects.get(user=user)
        
        return Response({"balance": str(wallet.balance)}, status=200)
    
    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found."}, status=404)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        if request.content_type != 'application/json':
            return Response({"error": "Content-Type must be application/json"}, status=status.HTTP_400_BAD_REQUEST)
        return super().post(request, *args, **kwargs)
    

class ExportTransactionsCSVView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Wallet', 'Sender', 'Receiver', 'Type', 'Amount', 'Timestamp'])

        transactions = Transaction.objects.filter(wallet__user=request.user)
        for tx in transactions:
            writer.writerow([tx.id, tx.wallet.address, tx.sender, tx.receiver, tx.transaction_type, tx.amount, tx.timestamp])

        return response

class TransactionListView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return Transaction.objects.filter(wallet=self.request.user.wallet)
    
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        receiver_wallet = request.data.get('receiver_wallet')
        text = request.data.get('text', '')  # فقط از متن استفاده می‌کنیم
        # فایل را حذف می‌کنیم چون نیازی به آن نداریم
        try:
            receiver = Wallet.objects.get(address=receiver_wallet).user
        except Wallet.DoesNotExist:
            return Response({"error": "Receiver wallet address not found"}, status=400)

        message = Message.objects.create(sender=request.user, receiver=receiver, text=text)  # بدون فایل
        return Response(MessageSerializer(message).data, status=201)
 
class SendFileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, wallet_address):
        try:
            receiver = Wallet.objects.get(address=wallet_address).user
        except Wallet.DoesNotExist:
            return Response({"error": "Receiver wallet address not found"}, status=404)

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=400)

        message = Message.objects.create(sender=request.user, receiver=receiver, text='', file=file)
        return Response(MessageSerializer(message).data, status=201)



class ChatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            chats = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user)) \
                .values('receiver__wallet__address', 'sender__wallet__address') \
                .annotate(
                    last_message=Max('text'),
                    timestamp=Max('timestamp'),
                    unread_count=Count('id', filter=Q(receiver=request.user, is_read=False))
                )

            chat_list = [
                {
                    "wallet_address": chat["receiver__wallet__address"] if chat["receiver__wallet__address"] != request.user.wallet.address else chat["sender__wallet__address"],
                    "last_message": chat["last_message"],
                    "timestamp": chat["timestamp"],
                    "unread_count": chat["unread_count"]
                }
                for chat in chats
            ]
            return Response(chat_list)
        
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ChatMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, wallet_address):
        try:
            chat_user = Wallet.objects.get(address=wallet_address).user
        except Wallet.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=chat_user)) |
            (Q(sender=chat_user) & Q(receiver=request.user))
        ).order_by('timestamp')

        messages.filter(receiver=request.user).update(is_read=True)

        return Response(MessageSerializer(messages, many=True).data)