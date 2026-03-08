from django.shortcuts import render, redirect

def create_new_password_page(request):

    return render(request, "create-new-password.html")