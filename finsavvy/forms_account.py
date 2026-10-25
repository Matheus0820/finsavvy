from django import forms

class CustomSignupForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control border-info text-dark', 'placeholder': 'Nome'})
    )

    def signup(self, request, user):
        user.first_name = self.cleaned_data.get('first_name')
        user.save()
        return user


