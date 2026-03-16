from django.urls import path

from .views import *

urlpatterns=[
    path('signup/',SignUpView.as_view()),
    path('code-verify/',CodeVerifyView.as_view()),
    path('get-new-code/',GetNewCode.as_view()),
    path('user-change-info/',UserChangeInfoView.as_view()),
    path('user-change-photo/',UserChangePhotoView.as_view()),
    path('login/',LoginView.as_view()),
    path('logout/',LogoutView.as_view()),
    path('refresh-token/',RefreshTokenView.as_view()),
    path('forgot-password/',ForgotPasswordView.as_view()),
    path('reset-code/',ResetPasswordCodeView.as_view()),
    path('reset-password/',ResetPasswordView.as_view()),
    path('post-create/',PostCreateView.as_view()),
    path('list-post/',PostListView.as_view()),
    path('post-update/<int:pk>/',PostUpdateView.as_view()),
    path('post-delete/<int:pk>/',PostDeleteView.as_view()),
]

