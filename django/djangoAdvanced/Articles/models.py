from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class Articles(models.Model):
    title = models.CharField(_("Title"), max_length=64)
    author = models.ForeignKey(User, verbose_name=_("Author"), on_delete=models.CASCADE)
    created = models.DateTimeField(_("Created at"), auto_now_add=True)
    synopsis = models.CharField(_("Synopsis"), max_length=312)
    content = models.TextField(_("Content"))
    def __str__(self):
        return self.title
    class Meta:
        db_table = "Articles"

class UserFavouriteArticle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    def __str__(self):
        return self.article.title
    class Meta:
        db_table = "UserFavouriteArticle"
        unique_together = ("user", "article")