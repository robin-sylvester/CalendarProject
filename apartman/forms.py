from apartman.models import Apartman
from django.contrib.auth import get_user_model
User = get_user_model()

from django import forms
import apartman

class UploadFileApartmanForm(forms.Form):
    file = forms.FileField()

    def clean(self):
        cleaned_data = super().clean()

        if not 'file' in cleaned_data:
            return cleaned_data
        else:
            file = cleaned_data['file']

        check = Apartman.objects.filter(url=file)

        if check:
            self.add_error('file', forms.ValidationError('Calendar with that name was already imported'))

class UploadURLApartmanForm(forms.Form):
    url = forms.CharField(max_length=255)

    def clean(self):
        cleaned_data = super().clean()

        if not 'url' in cleaned_data:
            return cleaned_data
        else:
            url = cleaned_data['url']

        check = Apartman.objects.filter(url=url)

        if check:
            self.add_error('url', forms.ValidationError('That URL was already imported'))
