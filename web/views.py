# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from web.models import FileUploadWeb


@never_cache
def FileUploadWebView(request):
    summarydictionary  = {}
    if request.method == 'POST':
        form = FileUploadWeb(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('The file is saved')
        else:
            print(form.errors)


    else:
        form = FileUploadWeb()
        summarydictionary['form'] = form

    return render(request, "addschool.html", {"summary": summarydictionary})

