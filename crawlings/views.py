from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Crawlings

Stock = get_user_model()

# Create your views here.
def index(request):
    company_info = request.GET.get('title')
    context = {
        'company_info': company_info,
    }
    return render(request, 'crawlings/index.html', context)

