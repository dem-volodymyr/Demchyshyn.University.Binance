from django import forms

class TwoFactorAuthForm(forms.Form):
    token = forms.IntegerField(min_value=0, max_value=999999)