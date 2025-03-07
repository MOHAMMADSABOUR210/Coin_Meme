from django.contrib.auth import login, logout, authenticate
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import LoginSerializer, RegisterSerializer, ProfileEditSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, Transaction
from decimal import Decimal
from .serializers import TransactionSerializer
from django.utils.dateparse import parse_date



@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # بررسی صحت اعتبار
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
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# لاگ‌اوت
@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})

# ویرایش پروفایل
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
@permission_classes([IsAuthenticated])  # فقط کاربران وارد شده می‌توانند پروفایل را ویرایش کنند
def profile_edit_view(request):
    user = request.user

    # بررسی اینکه آیا کاربر وارد شده است یا نه
    if user.is_anonymous:
        return Response({"error": "Authentication required to edit profile."}, status=status.HTTP_401_UNAUTHORIZED)

    # داده‌های ورودی را اعتبارسنجی می‌کنیم
    serializer = ProfileEditSerializer(user, data=request.data, partial=True)  # `partial=True` برای اختیاری بودن فیلدها
    if serializer.is_valid():
        serializer.save()  # ذخیره تغییرات
        return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    amount = request.data.get("amount")
    if not amount or Decimal(amount) <= 0:
        return Response({"error": "Invalid amount"}, status=400)

    wallet = request.user.wallet
    wallet.balance += Decimal(amount)
    wallet.save()

    Transaction.objects.create(wallet=wallet, transaction_type="deposit", amount=Decimal(amount))
    
    return Response({"message": "Deposit successful", "balance": wallet.balance})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    amount = request.data.get("amount")
    recipient_address = request.data.get("recipient_address")

    if not amount or Decimal(amount) <= 0:
        return Response({"error": "Invalid amount"}, status=400)

    sender_wallet = request.user.wallet

    try:
        receiver_wallet = Wallet.objects.get(address=recipient_address)
    except Wallet.DoesNotExist:
        return Response({"error": "Recipient wallet not found"}, status=404)

    if sender_wallet.balance < Decimal(amount):
        return Response({"error": "Insufficient balance"}, status=400)

    sender_wallet.balance -= Decimal(amount)
    receiver_wallet.balance += Decimal(amount)

    sender_wallet.save()
    receiver_wallet.save()

    Transaction.objects.create(wallet=sender_wallet, sender=sender_wallet, receiver=receiver_wallet, transaction_type="transfer", amount=Decimal(amount))
    Transaction.objects.create(wallet=receiver_wallet, sender=sender_wallet, receiver=receiver_wallet, transaction_type="receive", amount=Decimal(amount))

    return Response({"message": "Transfer successful", "balance": sender_wallet.balance})


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