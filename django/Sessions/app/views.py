from django.shortcuts import render, redirect
from django.conf import settings
from app.forms import LoginForm, TipForm
from app.models import User, Tip
import random
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import permission_required


def delete_tip(request):
    if request.POST.get("delete"):
        tip_id = request.POST.get("delete")
        tip = Tip.objects.get(id=tip_id)
        if request.user.has_perm('app.delete_tip') or request.user == tip.user or request.user.reputation >= 30:
            tip.user.reputation -= ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
            tip.user.save()
            tip.delete()

def downvote_tip(request):
    if request.POST.get("downvote"):
        tip_id = request.POST.get("downvote")
        tip = Tip.objects.get(id=tip_id)
        if request.user.has_perm('app.can_downvote_tip pour correction') or request.user == tip.user or request.user.reputation >= 15:
            if not request.user in tip.upvote.all():
                if not request.user in tip.downvote.all():
                    tip.downvote.add(request.user)
                    tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
                    tip.user.save()
                elif request.user in tip.downvote.all():
                    tip.downvote.remove(request.user)
                    tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
                    tip.user.save()
            elif request.user in tip.upvote.all():
                tip.downvote.add(request.user)
                tip.upvote.remove(request.user)
                tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
                tip.user.save()

def upvote_tip(request):
    if request.POST.get("upvote"):
        tip_id = request.POST.get("upvote")
        tip = Tip.objects.get(id=tip_id)
        if not request.user in tip.downvote.all():
            if not request.user in tip.upvote.all():
                tip.upvote.add(request.user)
                tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
                tip.user.save()
            elif request.user in tip.upvote.all():
                tip.upvote.remove(request.user)
                tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
                tip.user.save()
        elif request.user in tip.downvote.all():
            tip.upvote.add(request.user)
            tip.downvote.remove(request.user)
            tip.user.reputation = ((tip.upvote.count() * 5) + (tip.downvote.count() * -2))
            tip.user.save()

def index(request):
    login = False
    if request.user.is_authenticated:
        if request.method == 'POST':
            contenu = request.POST.get("contenu")
            myForm = TipForm(request.POST)
            if myForm.is_valid():
                Tip.objects.create(contenu=contenu, user=request.user)
            upvote_tip(request)
            downvote_tip(request)
            delete_tip(request)
        tip = Tip.objects.all()
        tip_user = Tip.objects.filter(user=request.user)
        reputation = 0
        if tip:
            for item in tip_user:
                reputation += ((item.upvote.count() * 5) + (item.downvote.count() * -2))
        login = True
        request.user.reputation = reputation
        tipform = TipForm()
        return render(request, 'ex/index.html', {"username": request.user.username, "login": login, "tip": tip, "reputation": request.user.reputation, "tipform": tipform})
    request.session.clear_expired()
    request.session.set_expiry(42)
    if 'username' not in request.session:
        request.session['username'] = random.choice(settings.USER_NAMES) 
    username = request.session['username']
    tip = Tip.objects.all()         
    return render(request, 'ex/index.html', {"username": username, "login": login, "tip": tip})

def deconnexion(request):
    logout(request)
    return redirect("index")
    

def subscribe(request):
    username = ''
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_verification = request.POST.get('password_verification')
        if (password != password_verification):
            return render(request, 'ex/subscribe.html', {"username": username, "error_message": 'Les mots de passe ne correspondent pas!'})
        myForm = LoginForm(request.POST)
        if myForm.is_valid():
            if User.objects.filter(username=username).exists():
                return render(request, 'ex/subscribe.html', {"username": username, "error_message": 'Le username existe deja!'})
            User.objects.create_user(username=username, password=password)
            return redirect("login_view")
        else:
            return render(request, 'ex/subscribe.html', {"username": username, "error_message": myForm.errors})    
    return render(request, 'ex/subscribe.html', {"username":username})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        myForm = LoginForm(request.POST)
        if myForm.is_valid():
           user = authenticate(request, username=username, password=password)
           if user:
            login(request, user)
            request.session.set_expiry(0)
            return redirect('/')
           else:
            return render(request, 'ex/login.html', {"username": username, "error_message": 'Username ou Mot de passe invalide!'})
        else:
            return render(request, 'ex/login.html', {"username": username, "error_message": myForm.errors})
    return render(request, 'ex/login.html')