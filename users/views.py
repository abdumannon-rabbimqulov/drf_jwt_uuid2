
from rest_framework.generics import CreateAPIView,UpdateAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import (
    CustomUser,CodeVerify,NEW,
    CODE_VERIFY,DONE,PHOTO_DONE,
    VIA_EMAIL,VIA_PHONE
    )
from .serializers import *
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from shared.views import send_email
from rest_framework_simplejwt.views import TokenObtainPairView

class SignUpView(CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = SingUpSerializers
    queryset = CustomUser

class CodeVerifyView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        user=request.user
        code=self.request.data.get('code')
        user_code=CodeVerify.objects.filter(code=code,user=user,
                                expiration_time__gte=datetime.now(),is_active=True
                                        )
        if not user_code.exists():
            raise ValidationError({
                'status':status.HTTP_400_BAD_REQUEST,
                'message':"Kodingiz xato yoki eskirgan"
            })
        else:
            user_code.update(is_active=False)

        if user.auth_status==NEW:
            user.auth_status=CODE_VERIFY
            user.save()

        response={
            'status':status.HTTP_200_OK,
            'message':'Kodingiz tasdiqlandi',
            'refresh':user.token()['refresh'],
            'access':user.token()['access']
        }
        return Response(response)


class GetNewCode(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        user=request.user
        if user.auth_type==VIA_EMAIL:
            code = send_email(user)
        elif user.auth_type==VIA_PHONE:
            code=user.generate_code(VIA_PHONE)
            print(code,'ppppppppppppppppppppppp')
        response={
            'status':status.HTTP_201_CREATED,
            'message':'Kodingiz yuborildi 2 minut vaqtizdan keyin ishlamaydi'
        }
        return Response(response)


class UserChangeInfoView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserChangeInfoSerializers
    queryset = CustomUser

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer=self.get_serializer(self.get_object(),data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response={
                "status": status.HTTP_201_CREATED,
                "message": "Siz muvaffaqiyatli ro'yxatdan o'tdiz!"
            },
        return Response(response)


class UserChangePhotoView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserPhotoSerializers
    queryset = CustomUser

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = {
            "status": status.HTTP_201_CREATED,
            "message": "Siz muvaffaqiyatli ro'yxatdan o'tdiz!"
        },
        return Response(response)

"""TokenObtainPairView bilan yozilgani!!!"""
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializers


"""APIView da yozilgan"""

# class LoginView(APIView):
#     permission_classes = (IsAuthenticated, )
#     def post(self,request):
#         user=self.request.user
#         serializer=LoginSerializers(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         data = {
#              "refresh":user.token()['refresh'],
#              "access": user.token()['access'],
#              "user": {
#                 "username": user.username,
#                  "email": user.email
#              }
#         }
#
#         return Response(data)