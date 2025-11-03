from django import forms

from .models import AdminPasswordResetRequest, Client


class AdminPasswordResetForm(forms.ModelForm):
    class Meta:
        model = AdminPasswordResetRequest
        fields = ['email', 'url']

    email = forms.EmailField(label='Email пользователя')
    url = forms.CharField(label='URL', required=False, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    def save(self, commit=True):
        instance = super().save(commit=False)
        try:
            instance.client = Client.objects.get(user__email=self.cleaned_data['email'])
        except Client.DoesNotExist:
            raise forms.ValidationError("Клиент с таким email не найден.")
        if commit:
            instance.save()
        return instance
