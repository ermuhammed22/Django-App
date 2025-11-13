from django.urls import path

from .views import process_get_view, user_form, handle_file_upload, upload_file

appname = 'requestdataapp'

urlpatterns = [
    path('get/', process_get_view, name='get-view'),
    path('bio/', user_form, name='user-form'),
    path('upload/', handle_file_upload, name='file-upload'),
    path('upload/', upload_file, name='upload_file'),
]