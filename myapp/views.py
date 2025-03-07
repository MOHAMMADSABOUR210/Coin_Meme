from django.contrib.auth import login, logout, authenticate
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .serializers import LoginSerializer,ProfileSerializer ,ProfileEditSerializer
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
    if request.method == 'POST':
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not email or not password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)

        wallet, created = Wallet.objects.get_or_create(user=user, defaults={"address": uuid.uuid4()})

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            "message": "User registered successfully.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "wallet_address": str(wallet.address)
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
    sender = request.user 
    receiver_address = request.data.get('receiver_address') 
    amount = request.data.get('amount')  

    if not receiver_address or not amount:
        return Response({"error": "Receiver address and amount are required."}, status=400)

    try:
        amount = Decimal(amount)

        sender_wallet = Wallet.objects.get(user=sender)
        
        if sender_wallet.balance < amount:
            return Response({"error": "Insufficient funds."}, status=400)

        receiver_wallet = Wallet.objects.get(address=receiver_address)

        Transaction.objects.create(
            wallet=sender_wallet,
            sender=sender_wallet,
            receiver=receiver_wallet,
            transaction_type='transfer',
            amount=amount
        )

        sender_wallet.balance -= amount
        sender_wallet.save()

        receiver_wallet.balance += amount
        receiver_wallet.save()

        return Response({"message": "Transfer successful."}, status=200)

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found."}, status=404)
    except ValueError:
        return Response({"error": "Invalid amount."}, status=400)



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
def deposit(request):
    user = request.user 
    amount = request.data.get('amount') 

    if amount is None or amount <= 0:
        return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(amount)
        
        wallet = Wallet.objects.get(user=user)
        
        wallet.balance += amount
        wallet.save()

        return Response({"message": f"Successfully deposited {amount}. New balance is {wallet.balance}."}, status=status.HTTP_200_OK)
    
    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
    

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