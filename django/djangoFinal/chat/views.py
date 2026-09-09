from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import *
from .models import *
from django.urls import reverse_lazy

def index(request):
    chatrooms = Chatroom.objects.all()
    return render(request, "chat/index.html", {"chatrooms":chatrooms})

def room(request, room_name):
    if request.user.is_authenticated:
        chatroom = Chatroom.objects.filter(name=room_name).first()
        if not chatroom:
            return redirect("index")
        return render(request, "chat/room.html", {"room_name": room_name})
    return redirect("account")

class CreateChatroom(CreateView):
    model = Chatroom
    fields = ['name']
    template_name = 'chat/chatroom_creation.html'
    success_url = reverse_lazy('index')

class CreateMessage(View):
    def post(self, request, **kwargs):
        roomname = request.POST.get('room_name')
        content = request.POST.get('content')
        chatroom = get_object_or_404(Chatroom, name=roomname)
        Message.objects.create(user=request.user, chatroom=chatroom, content=content)
        return redirect('room', room_name=roomname)