from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import os

from .forms import UserBioForm, UploadFileForm


MAX_FILE_SIZE = 5 * 1024 * 1024

def process_get_view(request: HttpRequest) -> HttpResponse:
    a = request.GET.get('a', '')
    b = request.GET.get('b', '')
    result = a + b
    context = {
        'a': a,
        'b': b,
        'result': result,
    }
    return render(request, 'requestdataapp/request-query-params.html', context=context)


def user_form (request: HttpRequest) -> HttpResponse:
    context = {
        'form': UserBioForm(),
    }
    return render(request, 'requestdataapp/user-bio-form.html', context=context)


def handle_file_upload(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # myfile = request.FILES['myfile']
            myfile = form.cleaned_data['file']
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            print('saved file', filename)
    else:
        form = UploadFileForm()

    context = {
        'form': form,
    }
    return render(request, 'requestdataapp/file-upload.html', context=context)


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            return JsonResponse({'error': 'No file provided.'}, status=400)

        if file.size > MAX_FILE_SIZE:
            return JsonResponse({'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB.'}, status=400)

        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.name)

        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        return JsonResponse({'message': 'File uploaded successfully.', 'file_name': file.name})

    return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)