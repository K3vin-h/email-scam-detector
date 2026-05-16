from django.urls import path

from gmail.auth import oauth_callback, start_oauth

urlpatterns = [
    path("gmail/", start_oauth, name="gmail-auth"),
    path("callback/", oauth_callback, name="gmail-callback"),
]
