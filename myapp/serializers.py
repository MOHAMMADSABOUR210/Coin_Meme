from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Transaction

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# Serializer برای ثبت‌نام
class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')  # حذف فیلد تکرار پسورد
        user = User.objects.create_user(**validated_data)
        return user

class ProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    # در اینجا تمام فیلدها اختیاری هستند
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        # بروزرسانی فیلدها فقط در صورت موجود بودن داده‌ها
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        
        instance.save()
        return instance
    

class TransactionSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.user.username", read_only=True)
    receiver_username = serializers.CharField(source="receiver.user.username", read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'timestamp', 'sender_username', 'receiver_username']