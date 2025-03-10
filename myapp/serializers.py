from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Transaction,Message

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']
    
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        
        instance.save()
        return instance
    

class ProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class TransactionSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.user.username", read_only=True)
    receiver_username = serializers.CharField(source="receiver.user.username", read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'timestamp', 'sender_username', 'receiver_username']


class MessageSerializer(serializers.ModelSerializer):
    sender_wallet_address = serializers.CharField(source='sender.wallet.address', read_only=True)
    receiver_wallet_address = serializers.CharField(source='receiver.wallet.address', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_wallet_address', 'receiver_wallet_address', 'text', 'file', 'timestamp', 'is_read']
class ChatListSerializer(serializers.Serializer):
    wallet_address = serializers.CharField()
    last_message = serializers.CharField()
    timestamp = serializers.DateTimeField()
    unread_count = serializers.IntegerField()