from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.serializers import LoginSerializer, RegisterSerializer, TokenSerializer, UserSerializer
from apps.common.errors import InvalidCredentials
from apps.common.serializers import errors


class _PublicAuthView(APIView):
    """No authentication on these routes (a stale token must not block signing in), but throttled."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(_PublicAuthView):
    @extend_schema(summary="Create an account", request=RegisterSerializer, responses={201: UserSerializer, **errors(409, 422, 429)})
    def post(self, request):  # noqa: ANN001, ANN201
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserSerializer(serializer.save()).data, status=201)


class LoginView(_PublicAuthView):
    @extend_schema(summary="Exchange email and password for an access token", request=LoginSerializer, responses={200: TokenSerializer, **errors(401, 422, 429)})
    def post(self, request):  # noqa: ANN001, ANN201
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Django's backend rejects inactive users and equalizes timing for unknown emails.
        user = authenticate(request, email=serializer.validated_data["email"], password=serializer.validated_data["password"])
        if user is None:
            raise InvalidCredentials("login rejected")
        return Response(
            {
                "access_token": str(AccessToken.for_user(user)),
                "token_type": "bearer",
                "expires_in_s": int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
            }
        )


class MeView(APIView):
    @extend_schema(summary="The signed-in user", responses={200: UserSerializer, **errors(401)})
    def get(self, request):  # noqa: ANN001, ANN201
        return Response(UserSerializer(request.user).data)
