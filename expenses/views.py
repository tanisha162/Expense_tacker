from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import ExpenseForm
from .models import Expense


def login_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('/')

        return render(
            request,
            'expenses/login.html',
            {'error': 'Invalid username or password'}
        )

    return render(request, 'expenses/login.html')


@login_required(login_url='/login/')
def index(request):

    expenses = Expense.objects.all()

    total = sum(exp.amount for exp in expenses)

    category_data = defaultdict(float)

    for exp in expenses:
        category_data[exp.category] += exp.amount

    labels = list(category_data.keys())
    values = list(category_data.values())

    context = {
        'expenses': expenses,
        'total': total,
        'labels': labels,
        'values': values,
    }

    return render(request, 'expenses/index.html', context)


@login_required(login_url='/login/')
def add_expense(request):

    if request.method == 'POST':

        form = ExpenseForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('/')

        return render(
            request,
            'expenses/add.html',
            {'error': 'Please check the highlighted fields and try again.'}
        )

    return render(request, 'expenses/add.html')


@login_required(login_url='/login/')
def delete_expense(request, pk):

    expense = get_object_or_404(Expense, id=pk)

    expense.delete()

    return redirect('/')


def logout_view(request):

    logout(request)

    return redirect('/login/')