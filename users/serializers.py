from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import CustomUser
from shared.utility import check_email_or_phone, check_email_or_phone_or_username
from .models import (
    VIA_PHONE,VIA_EMAIL,
    CODE_VERIFY,DONE,PHOTO_DONE
                     )
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.db.models import Q
from shared.views import send_email
from rest_framework_simplejwt.serializers import TokenObtainSerializer


class SingUpSerializers(serializers.ModelSerializer):
    id=serializers.UUIDField(read_only=True)
    auth_status=serializers.CharField(read_only=True)
    auth_type=serializers.CharField(read_only=True)
    email_or_phone = serializers.CharField(write_only=True)

    class Meta:
        model=CustomUser
        fields=('id','auth_status','auth_type','email_or_phone')



    def validate(self, attrs):
        super().validate(attrs)
        data=self.auth_validate(attrs)
        return data

    @staticmethod
    def auth_validate(user_input):
        user_input=user_input.get('email_or_phone')
        user_input_type=check_email_or_phone(user_input)
        if user_input_type=='phone':
            data={
                'auth_type':VIA_PHONE,
                'phone_number':user_input
            }
        elif user_input_type=='email':
            data={
                'auth_type':VIA_EMAIL,
                'email':user_input
            }
        else:
            response={
                'status':status.HTTP_400_BAD_REQUEST,
                'message':"email yoki telefon raqamiz xato"
            }
            raise ValidationError(response)
        return data

    def validate_email_or_phone(self,email_or_phone):
        user=CustomUser.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))
        if user:
            raise ValidationError({'message':'email yoki tel raqam band!'})
        return email_or_phone

    def create(self, validated_data):
        validated_data.pop('email_or_phone',None)
        user = CustomUser.objects.create(**validated_data)
        if user.auth_type==VIA_EMAIL:
            code=send_email(user)
        elif user.auth_type==VIA_PHONE:
            code=user.generate_code(VIA_PHONE)
            print(code,'ppppppppppppppppppppppp')
        else:
            raise ValidationError({
            'message':'yuborishda xato email yoki telefon raqaimni teshiring'
            })
        return user

    def to_representation(self, instance):
        data=super().to_representation(instance)
        data['message']='Kodingiz yuborildi'
        data['refresh']=instance.token()['refresh']
        data['access'] =instance.token()['access']
        return data


class UserChangeInfoSerializers(serializers.Serializer):
    first_name=serializers.CharField(required=True)
    last_name=serializers.CharField(required=True)
    username=serializers.CharField(required=True)
    password=serializers.CharField(required=True)
    conf_password=serializers.CharField(required=True)


    def validate(self,attrs):
        password=attrs.get('password')
        conf_password=attrs.get('conf_password')

        if  password!=conf_password:
            raise ValidationError({'message':'parollar mos emas'})
        elif len(password)<7:
            raise ValidationError({'message':'parol 8 ta belgidan kam bolmasligi kerak'})
        return attrs


    def validate_username(self,username):
        user_query = CustomUser.objects.filter(username=username)

        if user_query.exists():
            raise ValidationError({'message': 'Bu username band'})
        if len(username) < 6:
            raise ValidationError({'message': 'Username kamida 7 belgidan iborat bolishi kerek'})
        elif not username.isalnum():
            raise ValidationError({'message': 'username da ortiqcha belgi bolmasligi kerak '})
        elif username[0].isdigit():
            raise ValidationError({'message': 'username raqam bilan boshlanmasin '})
        return username

    def validate_first_name(self,first_name):

         if len(first_name)<3:
             raise ValidationError({'message':"first_name kamida 4 ta belgi bo'lishi kerak"})
         elif first_name.isdigit():
             raise ValidationError({'message':'first_name ortiqcha belig bolmasligi kerak'})
         elif not first_name.isalnum():
             raise ValidationError({'message': 'first_name da ortiqcha belgi bolmasligi kerak '})
         return first_name


    def update(self, instance, validated_data):
        validated_data.pop('conf_password')
        instance.username=validated_data.get('username')
        instance.first_name=validated_data.get('first_name')
        instance.last_name=validated_data.get('last_name')
        password=validated_data.get('password')
        instance.set_password(password)
        if instance.auth_status!=CODE_VERIFY:
            raise ValidationError({'message':'siz hali tasdiqlanmagansiz'})

        instance.auth_status=DONE
        instance.save()
        return instance


class UserPhotoSerializers(serializers.Serializer):
    photo=serializers.ImageField()

    def update(self, instance, validated_data):
        photo=validated_data.get('photo',None)
        if photo:
            instance.photo=photo
        if instance.auth_status==DONE or instance.auth_status==PHOTO_DONE :
            instance.auth_status=PHOTO_DONE
        else:
            raise ValidationError({'message':'Siz tasdiqlanmagansiz'})
        instance.save()
        return instance

class LoginSerializers(TokenObtainSerializer):
    password=serializers.CharField(required=True,write_only=True)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['user_input']=serializers.CharField(required=True,write_only=True)
        self.fields['username'] = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user=self.check_user_type(attrs)

        data ={
            "refresh":user.token()['refresh'],
            "access": user.token()['access'],
            "user": {
                "username": user.username,
                "email": user.email
            }
        }

        return data


    def check_user_type(self,data):
        password=data.get('password')
        user_input=data.get('user_input')
        user_input_type=check_email_or_phone_or_username(user_input)
        if user_input_type=='username':
            user=CustomUser.objects.filter(username=user_input).first()
            self.get_object(user)
            username=user.username
        elif user_input_type=='email':
            user=CustomUser.objects.filter(email=user_input).first()
            self.get_object(user)
            username=user.username

        elif user_input_type=='phone':
            user=CustomUser.objects.filter(phone_number=user_input).first()
            self.get_object(user)
            username=user.username
        else:
            raise ValidationError(detail='Malumot topilmadi')

        authentication_kwargs={
            "password":password,
            self.username_field:username
        }
        if user.auth_status not in [DONE,PHOTO_DONE]:
            raise ValidationError({'message':'siz hali toliq royxatdan otmagansiz '})

        user=authenticate(**authentication_kwargs)

        if not user:
            raise ValidationError('login yoki parol xato')

        return user


    def get_object(self,user):
        if not user:
            raise ValidationError({'message':'Xato malumot kiridingiz'})
        return True
"""Serializer ni o'zida yozilgan """
# class LoginSerializers(serializers.Serializer):
#     password=serializers.CharField(required=True,write_only=True)
#     user_input=serializers.CharField(required=True,write_only=True)
#     username_field=serializers.CharField(read_only=True)
#
#     def validate(self, attrs):
#         data=self.check_user_type(attrs)
#         return data
#
#
#     def check_user_type(self,data):
#         password=data.get('password')
#         user_input=data.get('user_input')
#         user_input_type=check_email_or_phone_or_username(user_input)
#         if user_input_type=='username':
#             user=CustomUser.objects.filter(username=user_input).first()
#             self.get_object(user)
#             username=user.username
#         elif user_input_type=='email':
#             user=CustomUser.objects.filter(email=user_input).first()
#             self.get_object(user)
#             username=user.username
#
#         elif user_input_type=='phone':
#             user=CustomUser.objects.filter(phone_number=user_input).first()
#             self.get_object(user)
#             username=user.username
#         else:
#             raise ValidationError(detail='Malumot topilmadi')
#
#         authentication_kwargs={
#             "password":password,
#             "username":username
#         }
#         if user.auth_status not in [DONE,PHOTO_DONE]:
#             raise ValidationError({'message':'siz hali toliq royxatdan otmagansiz '})
#
#         user=authenticate(**authentication_kwargs)
#
#         if not user:
#             raise ValidationError('login yoki parol xato')
#
#         return user
#
#
#     def get_object(self,user):
#         if not user:
#             raise ValidationError({'message':'Xato malumot kiridingiz'})
#         return True
#

class ForgotPasswordSerializers(serializers.Serializer):
    user_input=serializers.CharField(required=True,write_only=True)

    def validate(self, attrs):
        user_data=attrs.get('user_input',None)
        if not user_data:
            raise ValidationError({'message':'email,username yoki telefon raqam kiriting'})
        user=CustomUser.objects.filter(
            Q(username=user_data) | Q(email=user_data) | Q(phone_number=user_data)).first()
        if not user:
            raise ValidationError(detail="xato malumot kiritdingiz yoki ro'yxatdan o'tmagansiz")
        user_type=check_email_or_phone_or_username(user_data)

        if user_type=='phone':
            code = user.generate_code(VIA_PHONE)
            print(code, 'ppppppppppppppppppppppp')
        elif user_type=='email':
            code=send_email(user)
        elif user_type=='username':
            if user.phone_number:
                code = user.generate_code(VIA_PHONE)
                print(code, 'ppppppppppppppppppppppp')
            elif user.email:
                code = send_email(user)
            else:
                raise ValidationError(detail="siz to'liq ro'yxatdan o'tmagansiz ")

        response={
            'status':status.HTTP_201_CREATED,
            'message':'Kodingiz yuborildi',
            'refresh':user.token()['refresh'],
            'access':user.token()['access']
        }
        return response




class ResetPasswordSerializers(serializers.Serializer):
    password=serializers.CharField(required=True,write_only=True)
    conf_password=serializers.CharField(required=True,write_only=True)

    def validate(self, attrs):
        password=attrs.get('password')
        conf_password=attrs.get('conf_password')
        if  password!=conf_password:
            raise ValidationError({'message':'parollar mos emas'})
        elif len(password)<7:
            raise ValidationError({'message':'parol 8 ta belgidan kam bolmasligi kerak'})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('conf_password')
        password=validated_data.get('password')
        instance.set_password(password)
        instance.save()
        return instance

