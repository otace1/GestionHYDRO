from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
@login_required(login_url='login')
def app_settings(request):
    return render(request, 'app_settings.html')