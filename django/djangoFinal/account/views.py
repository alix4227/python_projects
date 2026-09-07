from django.shortcuts import render, redirect
from django.views.generic import *
from .models import *
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth.views import *
from django.contrib.auth import login, logout
from django.contrib.auth.forms import *
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import *
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# def handler404(request, exception):
#    return render(request, '404handler.html')

class Register(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('account')
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account')
        return super().dispatch(request, *args, **kwargs)

class Login(FormView):
    model = User
    form_class = CustomAuthenticationForm
    template_name = 'account/base.html'
    success_url = reverse_lazy('http://localhost:8000/chat/')
    def post(self, request, **kwargs):
        content_type = request.content_type or ''
        if 'application/json' in content_type:
            data = json.loads(request.body)
            payload = data.get('payload', {})
            user = authenticate(request, username=payload['username'], password=payload['password'])
            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'User logged!', 'username':user.username})
            return JsonResponse({'status': 'User not logged!'}, status=401)
        return super().post(request, **kwargs)
    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)
    
class Logout(View):
    def get(self, request, **kwargs):
        logout(self.request)
        return redirect('account')
    def post(self, request, **kwargs):
        logout(self.request)
        return JsonResponse({'status': 'User logged out!'})