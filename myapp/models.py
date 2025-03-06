import uuid
from django.db import models
from django.contrib.auth.models import User

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    address = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet of {self.user.username} - Balance: {self.balance}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),  # افزایش اعتبار
        ('transfer', 'Transfer'),  # انتقال وجه
        ('receive', 'Receive'),  # دریافت وجه
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    sender = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_transactions")
    receiver = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"
