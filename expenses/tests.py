from django.contrib.auth.models import User
from django.test import TestCase

from .models import Expense


class AddExpenseValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')
        self.valid_data = {
            'title': 'Groceries',
            'amount': '450',
            'category': 'Food',
            'date': '2026-11-15',
            'note': '',
        }

    def test_non_numeric_amount_does_not_crash(self):
        # Regression test: float('abc') used to raise ValueError -> 500.
        data = {**self.valid_data, 'amount': 'abc'}
        response = self.client.post('/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertContains(response, 'Please check')

    def test_invalid_date_does_not_crash(self):
        # Regression test: an unparseable date used to raise
        # ValidationError -> 500.
        data = {**self.valid_data, 'date': 'not-a-date'}
        response = self.client.post('/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertContains(response, 'Please check')

    def test_valid_expense_is_created(self):
        response = self.client.post('/add/', self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(Expense.objects.first().amount, 450.0)


class DeleteExpenseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')

    def test_delete_missing_expense_returns_404(self):
        # Regression test: Expense.objects.get() used to raise
        # DoesNotExist -> 500 for an unknown id.
        response = self.client.post('/delete/9999/')
        self.assertEqual(response.status_code, 404)

    def test_get_does_not_delete_expense(self):
        # Regression test: delete used to run on a plain GET, so any
        # link click, prefetch or crawler could wipe an expense.
        expense = Expense.objects.create(
            title='Lunch', amount=200, category='Food',
            date='2026-11-15',
        )
        response = self.client.get(f'/delete/{expense.id}/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Expense.objects.filter(id=expense.id).exists())

    def test_post_deletes_expense(self):
        expense = Expense.objects.create(
            title='Lunch', amount=200, category='Food',
            date='2026-11-15',
        )
        response = self.client.post(f'/delete/{expense.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())
