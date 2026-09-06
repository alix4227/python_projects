from django.test import TestCase
from .models import *
from django.urls import reverse

class ArticlesModelTests(TestCase):


    #----------Test Publications--------------------------------------------------------------------------------------------------

    def test_publications_with_login(self):
        user = User.objects.create_user(username='ALIX', password="Djangouser27!")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("publications"))
        self.assertEqual(response.status_code, 200, msg=f"Test Publications avec login: Expected 200, got {response.status_code}")
    def test_publications_without_login(self):
        response = self.client.get(reverse("publications"))
        self.assertEqual(response.status_code, 302, msg=f"Test Publications sans login: Expected 302, got {response.status_code}")
    

    #----------Test Favourites--------------------------------------------------------------------------------------------------

    def test_favourites_with_login(self):
        user = User.objects.create_user(username='ALIX', password="Djangouser27!")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("favourites"))
        self.assertEqual(response.status_code, 200, msg=f"Test Favourites avec login: Expected 200, got {response.status_code}")
    def test_favourites_without_login(self):
        response = self.client.get(reverse("favourites"))
        self.assertEqual(response.status_code, 302, msg=f"Test Favourites sans login: Expected 302, got {response.status_code}")


    #----------Test Publish--------------------------------------------------------------------------------------------------

    def test_publish_with_login(self):
        user = User.objects.create_user(username='ALIX', password="Djangouser27!")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("createArticle"))
        self.assertEqual(response.status_code, 200, msg=f"Test Publish avec login: Expected 200, got {response.status_code}")
    def test_publish_without_login(self):
        response = self.client.get(reverse("createArticle"))
        self.assertEqual(response.status_code, 302, msg=f"Test Publish sans login: Expected 302, got {response.status_code}")


    #----------Test Register--------------------------------------------------------------------------------------------------
    def test_register_with_login(self):
        user = User.objects.create_user(username='ALIX', password="Djangouser27!")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 302, msg=f"Test Register avec login: Expected 302, got {response.status_code}")
    def test_register_without_login(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200, msg=f"Test Register avec login: Expected 200, got {response.status_code}")
    
    #----------Test Favourites--------------------------------------------------------------------------------------------------
    def test_add_to_favourite_with_login(self):
        user = User.objects.create_user(username='ALIX', password="Djangouser27!")
        user.save()
        self.client.force_login(user)
        article = Articles.objects.create(title='Test', author=user, synopsis="Test", content="Test")
        UserFavouriteArticle.objects.create(user=user, article=article)
        response = self.client.post(reverse("addFavourite", kwargs={'pk': article.id}), {'article': article.id})
        self.assertEqual(response.status_code, 400, msg=f"Test add_Favourites avec login: Expected 400, got {response.status_code}")