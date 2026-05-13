from django.shortcuts import render, redirect


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == 'admin' and password == 'admin123':
            return redirect('/')

        return render(request, 'expenses/login.html', {'error': 'Invalid credentials'})

    return render(request, 'expenses/login.html')


def index(request):
    return render(request, 'expenses/index.html')

def add_expense(request):
    return render(request, 'expenses/add.html')

def delete_expense(request, pk):
    return redirect('/')


def logout_view(request):
    return redirect('/login/')