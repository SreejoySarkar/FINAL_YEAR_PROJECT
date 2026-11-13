from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class VerifyOTPSerializer(serializers.Serializer):
    otp_session = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()