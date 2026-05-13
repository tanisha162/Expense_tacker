from django.shortcuts import render, redirect

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == 'admin' and password == 'admin123':
            return redirect('/')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')
def index(request):
    return redirect('/login/')