from django.shortcuts import render,HttpResponse
from rbac.models import User
from rbac.service.perssions import initial_session
# Create your views here.
def login(request):
    if request.method =="POST":
        username = request.POST.get("user")
        pwd =request.POST.get("pwd")
        user = User.objects.filter(name=username,pwd=pwd).first()
        print(user)
        if user:
            request.session["user_id"]=user.pk
            request.session["user_name"]=user.name
            initial_session(user,request)
            return HttpResponse("登陆成功")

    return render(request,"login.html")
