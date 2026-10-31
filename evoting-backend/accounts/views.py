import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from audit.services import log_event
from .models import Admin, AdminOTP
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    VerifyOTPSerializer,
)

OTP_SALT = "admin-otp-session"
OTP_VALID_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        admin = authenticate(
            username=s.validated_data["username"],
            password=s.validated_data["password"]
        )

        if admin is None or not admin.is_active:
            log_event(
                "ADMIN_LOGIN_FAILED",
                None,
                {"username": s.validated_data["username"]},
                request
            )

            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        code = f"{secrets.randbelow(1_000_000):06d}"

        AdminOTP.objects.filter(
            admin=admin,
            used=False
        ).update(used=True)

        AdminOTP.objects.create(
            admin=admin,
            code_hash=make_password(code),
            expires_at=timezone.now() + timedelta(
                minutes=OTP_VALID_MINUTES
            )
        )

        send_mail(
            "Your e-voting admin OTP",
            f"Your code is {code}. It expires in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [admin.email]
        )

        session = signing.dumps(
            {"admin_id": admin.id},
            salt=OTP_SALT
        )

        log_event("ADMIN_LOGIN_PASSWORD_OK", admin, {}, request)

        return Response({
            "otp_required": True,
            "otp_session": session
        })


class AdminVerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            data = signing.loads(
                s.validated_data["otp_session"],
                salt=OTP_SALT,
                max_age=OTP_VALID_MINUTES * 60
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Session expired. Log in again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        admin = Admin.objects.get(id=data["admin_id"])

        otp = (
            AdminOTP.objects
            .filter(admin=admin, used=False)
            .order_by("-created_at")
            .first()
        )

        if (
            otp is None
            or otp.expires_at < timezone.now()
            or otp.attempts >= MAX_OTP_ATTEMPTS
        ):
            return Response(
                {"detail": "OTP expired or locked. Log in again."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(
            s.validated_data["otp"],
            otp.code_hash
        ):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])

            log_event("ADMIN_OTP_FAILED", admin, {}, request)

            return Response(
                {"detail": "Wrong OTP."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        otp.used = True
        otp.save(update_fields=["used"])

        refresh = RefreshToken.for_user(admin)

        log_event("ADMIN_LOGIN_SUCCESS", admin, {}, request)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": admin.role,
            "username": admin.username,
        })


class AdminLogoutView(APIView):
    def post(self, request):
        s = LogoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            RefreshToken(
                s.validated_data["refresh"]
            ).blacklist()

        except TokenError:
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        log_event("ADMIN_LOGOUT", request.user, {}, request)

        return Response(status=status.HTTP_204_NO_CONTENT)
