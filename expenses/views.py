from collections import defaultdict
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

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

    expenses = Expense.objects.filter(user=request.user)

    # Decimal arithmetic: amounts are money, so totals must be exact.
    # Summing FloatField values gave binary-float artefacts on the
    # dashboard (0.1 + 0.2 rendered as 0.30000000000000004).
    total = sum((exp.amount for exp in expenses), Decimal('0'))

    category_data = defaultdict(Decimal)

    for exp in expenses:
        category_data[exp.category] += exp.amount

    labels = list(category_data.keys())
    # Chart.js takes JSON numbers; Decimals are not JSON-serialisable,
    # so convert the exact per-category totals to floats for the chart.
    values = [float(v) for v in category_data.values()]

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

            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

            return redirect('/')

        return render(
            request,
            'expenses/add.html',
            {'error': 'Please check the highlighted fields and try again.'}
        )

    return render(request, 'expenses/add.html')


@login_required(login_url='/login/')
@require_POST
def delete_expense(request, pk):

    expense = get_object_or_404(Expense, id=pk, user=request.user)

    expense.delete()

    return redirect('/')


@require_POST
def logout_view(request):
    # POST-only: a GET logout lets any third-party page (or a link
    # prefetcher/crawler) log the user out with a bare <img> tag.
    # Django's own logout view requires POST for the same reason.
    logout(request)

    return redirect('/login/')