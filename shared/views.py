from django.core.mail import send_mail
from users.models import CodeVerify,CustomUser,VIA_EMAIL
from datetime import datetime
from rest_framework.exceptions import ValidationError
from conf import settings
import random
# Create your views here.

def send_email(user):
    active_codes=CodeVerify.objects.filter(user=user,expiration_time__gte=datetime.now())
    if active_codes.exists():
        raise ValidationError({'message':'sizda active code bor'})
    code =random.randint(1000,9999)
    CodeVerify.objects.create(
        code=code,
        user=user,
        verify_type=VIA_EMAIL
    )

    try:
        send_mail(
            "Tasdiqlash kodi",
            f" Sizning tasdiqlash kodingiz {code}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently = False,
        )
        return True
    except Exception as e:
        raise ValidationError({'message':f" Email yuborishda xatolik: {e}"})
