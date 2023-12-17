from django import forms

from file_upload.models import SchoolImage


class FileUploadWeb(forms.ModelForm):
    class Meta:
        model = SchoolImage
        exclude = ()

