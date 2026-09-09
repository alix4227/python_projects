from django.shortcuts import render, redirect
from django.views.generic import *
from .models import *
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth.views import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import *
from .forms import *
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import *


# def handler404(request, exception):
#    return render(request, '404handler.html')

class ArticlesListView(ListView):
    model = Articles
    context_object_name = "articles_objects"
    template_name = "articles.html"
    ordering = ['-created']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        for article in context["articles_objects"]:
            delta = now - article.created
            article.when = str(delta).split('.')[0]
        context["headers"] = [_("ID"),_("Title"), _("Author"), _("Created at"), _("Synopsis"), _("When")]
        return context

class ArticleCreateView(CreateView):
    
    model = Articles
    fields = ['title', 'synopsis', 'content']
    template_name = 'article_creation.html'
    success_url = reverse_lazy('articles')
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class UserCreationView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'user_creation.html'
    success_url = reverse_lazy('login')
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class Login(FormView):
    model = User
    form_class = CustomAuthenticationForm
    template_name = 'login.html'
    success_url = reverse_lazy('home')
    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user is None:
            form.add_error(None, "Identifiants invalides")
            return self.form_invalid(form)
        login(self.request, user)
        return super().form_valid(form)
    

class Home(RedirectView):
    pattern_name = 'articles'

class Publications(ListView):
    model = Articles
    context_object_name = "articles_objects"
    template_name = "publications.html"
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["headers"] = [f.name for f in Articles._meta.fields if f.name not in ('content', 'id', 'author')]
        return context
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class Detail(DetailView):
    model = Articles
    context_object_name = "item"
    template_name = 'detail.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["headers"] = [f.name for f in Articles._meta.fields]
        return context
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    

class Logout(TemplateView):
    def get(self, request, **kwargs):
        logout(self.request)
        return redirect('home')

class Favourites(ListView):
    model = UserFavouriteArticle
    context_object_name = "favourites"
    template_name = "favourites.html"
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class FavouriteCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        return redirect('detail', pk=pk)
    def post(self, request, *args, **kwargs):
        article = Articles.objects.get(pk=request.POST.get('article'))
        already_favourite = UserFavouriteArticle.objects.filter(user=request.user, article=article).exists()
        if already_favourite: 
            return render(request, "favourite_already_exists.html", status=409)
        UserFavouriteArticle.objects.create(user=request.user, article=article)
        return redirect('favourites')
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)