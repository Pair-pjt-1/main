from django import forms
from .models import Crawlings

class CrawlingForm(forms.Form):
    class Meta():
        model = Crawlings
        fields = '__all__'