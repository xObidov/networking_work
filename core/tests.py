from django.test import TestCase
from django.urls import reverse

from core.testing import make_user


class I18nTests(TestCase):
    """Uzbek language support: switcher endpoint + translated UI."""

    def setUp(self):
        self.user = make_user(email="i18n@test.local")
        self.client.force_login(self.user)

    def _switch(self, language):
        return self.client.post(
            reverse("set_language"), {"language": language, "next": "/"}
        )

    def test_switch_to_uzbek_translates_sidebar(self):
        self._switch("uz")
        response = self.client.get(reverse("customers:list"))
        self.assertContains(response, "Mijozlar")          # Customers
        self.assertContains(response, "Boshqaruv paneli")  # Dashboard
        self.assertContains(response, "Mijoz qo‘shish")  # Add Customer

    def test_switch_back_to_english(self):
        self._switch("uz")
        self._switch("en")
        response = self.client.get(reverse("customers:list"))
        self.assertContains(response, "Add Customer")

    def test_model_choice_labels_translated(self):
        self._switch("uz")
        response = self.client.get(reverse("tasks:list"))
        # Status choices in the filter dropdown come from the model labels
        self.assertContains(response, "Kutilmoqda")   # Pending
        self.assertContains(response, "Jarayonda")    # In Progress

    def test_login_page_in_uzbek(self):
        self.client.logout()
        self._switch("uz")
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "CRM tizimiga kirish")
        self.assertContains(response, "Meni eslab qol")

    def test_language_switcher_rendered(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertContains(response, 'action="/i18n/setlang/"')
        self.assertContains(response, "Oʻzbekcha")
