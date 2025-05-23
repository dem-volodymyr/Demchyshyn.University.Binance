from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    birthday = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    # gender field is now a true gender field from the model

    class Meta:
        model = Profile
        fields = '__all__'
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields:
            if field == 'gender':
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            elif field == 'avatar':
                self.fields[field].widget.attrs.update({'class': 'custom-file-input', 'id': 'id_avatar'})
            elif field == 'birthday':
                self.fields[field].widget.attrs.update({'class': 'form-control', 'type': 'date'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs['placeholder'] = 'Ваше імʼя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Ваше прізвище'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'        