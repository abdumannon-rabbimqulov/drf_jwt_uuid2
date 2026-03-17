from rest_framework.generics import (CreateAPIView,
                                     UpdateAPIView, ListAPIView,
                                     RetrieveAPIView, DestroyAPIView, get_object_or_404
                                     )
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework import permissions
from .serializers import *
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from shared.views import send_email
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken



class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.auth==request.user

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



class LogoutView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self,request):
        refresh=self.request.data.get('refresh')
        try:
            refresh_token=RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError(detail=f" xatolik {e}")
        else:
            response={
                'status':status.HTTP_200_OK,
                'message':"Siz logout qildiz"
            }
        return Response(response)


class RefreshTokenView(APIView):
    def post(self,request):
        refresh=self.request.data.get('refresh')
        try:
            refresh_token=RefreshToken(refresh)
        except Exception as e:
            raise ValidationError(detail=f"xato yoki vaqti tugadi {e}")
        else:
            response={
                'status':status.HTTP_200_OK,
                'message':'sizni tokeniz yangilandi',
                'access':str(refresh_token.access_token)
            }
        return Response(response)


class ForgotPasswordView(APIView):
    permission_classes = (AllowAny, )
    def post(self,request):
        serializer=ForgotPasswordSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.validated_data
        response = {
            'status': status.HTTP_200_OK,
            "message": response_data.get('message'),
            "access": response_data.get('access'),
            "refresh": response_data.get('refresh'),
        }
        return Response(response)


class ResetPasswordCodeView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        code=self.request.data.get('code')
        user=self.request.user
        user_code = CodeVerify.objects.filter(code=code, user=user,
                                              expiration_time__gte=datetime.now(), is_active=True
                                              )
        if not user_code.exists():
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Kodingiz xato yoki eskirgan"
            })
        else:
            user_code.update(is_active=False)


        response = {
            'status': status.HTTP_200_OK,
            'message': 'Kodingiz tasdiqlandi',
        }
        return Response(response)



class ResetPasswordView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        user=request.user
        serializer=ResetPasswordSerializers(data=request.data,instance=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response={
            'status':status.HTTP_200_OK,
            'message':"Siz muffaqiyatli parolizni tikladiz",
        }
        return Response(response)

"""         Post        """


class PostCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def perform_create(self, serializer):
        serializer.save(auth=self.request.user)

class PostUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def update(self, request, *args, **kwargs):
        instance=self.get_object()

        if instance.auth!=request.user:
            raise ValidationError({'message':"Siz o'zingizning postingizni update qila olasiz"})

        serializer=self.get_serializer(instance,data=request.data,partial=True)

        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        response={
            'status':status.HTTP_200_OK,
            'message':'malumotlar yangilandi',
            'data':serializer.validated_data
        }

        return Response(response)


    def perform_update(self, serializer):
        serializer.save()

class PostListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializers

    def get_queryset(self):
        user=self.request.user
        return Post.objects.filter(auth=user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)

        response={
            'status':status.HTTP_200_OK,
            'message':'sizning postlariz',
            "user": request.user.username,
            'data':serializer.data
        }
        return Response(response)

class PostDeleteView(DestroyAPIView):
    permission_classes = (IsAuthenticated,IsAuthor)
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            response={
                'status':status.HTTP_200_OK,
                'message':"malumot o'chirildi",
            }
        except Exception:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "malumot topilmadi",
            }
        return Response(response)


class PostDetailView(APIView):
    permission_classes = (IsAuthenticated,AllowAny)
    def get(self,request,pk):
        post=get_object_or_404(Post,id=pk)

        serializer=PostDetailSerilaizers(post,context={'request': request})


        response={
            "status":status.HTTP_200_OK,
            "message":"malumotlar",
            'data':serializer.data
        }

        return Response(response)
    def post(self,request,pk):
        user=self.request.user

        if not user.is_authenticated:
            raise ValidationError({'message':"siz ro'yxatdan o'tmagansiz "})

        postlike, Like=PostLike.objects.get_or_create(
            auth=user,
            post_id=pk,
        )

        if not Like:
            postlike.delete()
            return Response({'message':"like o'chirildi"})

        response={
            'status':status.HTTP_201_CREATED,
            "message":"like bosildi"
        }
        return Response(response)

"""          Comment      """


class CommentCreateView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        post_id=self.request.data.get('post_id')
        text=self.request.data.get('text')
        post=get_object_or_404(Post,id=post_id)
        comment=Comment.objects.create(
            auth=self.request.user,
            post_id=post_id,
            text=text
        )

        response={
            'status':status.HTTP_201_CREATED,
            'message':'comment qoshildi',
            'comment':comment.id
        }

        return Response(response)

class CommentUpdateView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        comment_id=self.request.data.get('comment_id')
        new_text=self.request.data.get('text')
        comment=Comment.objects.get(id=comment_id,auth=self.request.user)
        comment.text=new_text
        comment.save()

        response={
            'status':status.HTTP_200_OK,
            'message':'comment yangilandi',
        }
        return Response(response)

class CommentListView(ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = CommentSerializers

    def get_queryset(self):
        user=self.request.user
        return Comment.objects.filter(auth=user)

class CommentDeleteView(APIView):
    permission_classes = (IsAuthenticated,IsAuthor)
    def post(self,request):
        user=self.request.user
        comment_id=self.request.data.get("comment_id")
        comment=get_object_or_404(Comment,id=comment_id,auth=user)
        comment.delete()

        response={
            'status':status.HTTP_200_OK,
            'message':"malumot o'chirildi"
        }
        return Response(response)


