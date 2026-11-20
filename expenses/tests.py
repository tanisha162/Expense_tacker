from decimal import Decimal

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

    def test_negative_amount_is_rejected(self):
        # Regression test: a negative amount used to be accepted, so a
        # -450 "expense" was saved and subtracted from the dashboard
        # total and the category pie chart.
        data = {**self.valid_data, 'amount': '-450'}
        response = self.client.post('/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertContains(response, 'Please check')

    def test_zero_amount_is_rejected(self):
        # Regression test: a zero-amount expense used to be accepted
        # and saved as a meaningless ledger row.
        data = {**self.valid_data, 'amount': '0'}
        response = self.client.post('/add/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertContains(response, 'Please check')


class AddExpenseFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')

    def test_amount_input_accepts_decimal_amounts(self):
        # Regression test: the amount input was <input type="number">
        # with no step attribute, so browsers defaulted step to 1 and
        # rejected decimal amounts like 19.99 with a step-mismatch
        # error — the form could never be submitted for a paise-level
        # amount, even though the backend stores Decimal amounts.
        response = self.client.get('/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'step="0.01"')


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
            date='2026-11-15', user=self.user,
        )
        response = self.client.get(f'/delete/{expense.id}/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Expense.objects.filter(id=expense.id).exists())

    def test_post_deletes_expense(self):
        expense = Expense.objects.create(
            title='Lunch', amount=200, category='Food',
            date='2026-11-15', user=self.user,
        )
        response = self.client.post(f'/delete/{expense.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())


class ExpenseOwnershipTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pw123456')
        self.bob = User.objects.create_user('bob', password='pw123456')
        self.client.login(username='alice', password='pw123456')
        self.valid_data = {
            'title': 'Groceries',
            'amount': '450',
            'category': 'Food',
            'date': '2026-11-15',
            'note': '',
        }

    def test_added_expense_belongs_to_creator(self):
        # Regression test: expenses used to be ownerless, so every
        # logged-in user saw (and could delete) everyone else's data.
        response = self.client.post('/add/', self.valid_data)
        self.assertEqual(response.status_code, 302)
        expense = Expense.objects.first()
        self.assertEqual(expense.user, self.alice)

    def test_user_cannot_see_other_users_expenses(self):
        self.client.post('/add/', self.valid_data)
        self.client.logout()
        self.client.login(username='bob', password='pw123456')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Groceries')
        self.assertNotContains(response, '450')

    def test_user_cannot_delete_other_users_expense(self):
        self.client.post('/add/', self.valid_data)
        expense = Expense.objects.first()
        self.client.logout()
        self.client.login(username='bob', password='pw123456')
        response = self.client.post(f'/delete/{expense.id}/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(id=expense.id).exists())


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')

    def test_get_does_not_log_out(self):
        # Regression test: logout used to run on a plain GET, so any
        # third-party page, link prefetcher or crawler could log the
        # user out with a bare <img> tag.
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_logs_out(self):
        response = self.client.post('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)


class DashboardMoneyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')

    def test_dashboard_total_is_exact_not_float_artefact(self):
        # Regression test: amount was a FloatField, so the dashboard
        # total summed binary floats and 0.1 + 0.2 rendered as
        # "₹ 0.30000000000000004" instead of "₹ 0.30".
        Expense.objects.create(
            title='Tea', amount='0.1', category='Food',
            date='2026-11-15', user=self.user,
        )
        Expense.objects.create(
            title='Snack', amount='0.2', category='Food',
            date='2026-11-15', user=self.user,
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '₹ 0.30')
        self.assertNotContains(response, '0.30000000000000004')

    def test_amount_is_stored_as_decimal(self):
        # Regression test: amounts were stored as binary floats.
        Expense.objects.create(
            title='Tea', amount='19.99', category='Food',
            date='2026-11-15', user=self.user,
        )
        self.assertEqual(
            Expense.objects.first().amount, Decimal('19.99')
        )

    def test_category_chart_values_are_exact(self):
        # Regression test: per-category totals were also summed as
        # floats, so the pie-chart data carried the same artefact.
        Expense.objects.create(
            title='Tea', amount='0.1', category='Food',
            date='2026-11-15', user=self.user,
        )
        Expense.objects.create(
            title='Snack', amount='0.2', category='Food',
            date='2026-11-15', user=self.user,
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '0.30000000000000004')


class DashboardChartEscapingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw123456')
        self.client.login(username='tester', password='pw123456')

    def test_malicious_category_cannot_break_out_of_chart_script(self):
        # Regression test: category labels were rendered into the
        # dashboard's <script> block with |safe, so a category like
        # "</script><script>alert(1)</script>" closed the script tag
        # and ran as stored XSS for every viewer of the dashboard.
        Expense.objects.create(
            title='Evil', amount=10,
            category='</script><script>alert("xss")</script>',
            date='2026-11-16',
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, '</script><script>alert', status_code=200
        )
        # The chart data must still reach the page, safely encoded.
        self.assertContains(response, 'expense-labels')
