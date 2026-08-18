from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, MyPageSerializer, SignupSerializer


def _first_error_code(errors):
    for field_errors in errors.values():
        for err in field_errors:
            return str(err)
    return "invalid_request"


class SignupView(APIView):

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            error_code = _first_error_code(serializer.errors)
            if error_code == "email_already_exists":
                return Response({"error": "email_already_exists"}, status=status.HTTP_409_CONFLICT)
            if error_code not in (
                "invalid_password_format",
                "invalid_nickname_length",
                "invalid_email_format",
            ):
                error_code = "invalid_request"
            return Response({"error": error_code}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response(
            {"token": token.key, "nickname": user.nickname},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            error_code = _first_error_code(serializer.errors)
            if error_code == "invalid_credentials":
                return Response({"error": "invalid_credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({"error": "invalid_request"}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "nickname": user.nickname}, status=status.HTTP_200_OK)


class MyPageView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MyPageSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)