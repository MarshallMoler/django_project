from django.urls import re_path
from . import views


urlpatterns=[
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$',views.ImagecodeView.as_view()),
]