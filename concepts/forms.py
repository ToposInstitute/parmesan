from django import forms
from django.utils.translation import gettext as _
from .models import *

def get_collections():

    return Collection.objects.all()

class SearchForm(forms.Form):
    """
    The default Parmesan search form, which allows the user to construct a
    query for searching data in a contextual corpus.
    """

    template_name = "concepts/search_form.html"

    query = forms.CharField(
        label=_("Query"),
        required=True,
    )

    collections = forms.ModelMultipleChoiceField(
        Collection.objects.all().order_by('-priority'),
        label=_("Collections"),
        initial=Collection.objects.all(),
    )
