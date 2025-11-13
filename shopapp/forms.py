from django import forms
from django.contrib.auth.models import Group
from django.forms import ModelForm

from .models import Product, ProductImage, Order
from .widgets import MultiFileInput


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'discount', 'preview']


# class ProductMultipleForm(forms.Form):
#     images = forms.FileField(
#         widget=forms.FileInput(attrs={'multiple': True}),
#         required=False,
#     )


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = 'user', 'products', 'promocode', 'delivery_address'


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = 'name', 'permissions'


class CSVImportForm(forms.Form):
    csv_file = forms.FileField()
