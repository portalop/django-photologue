from django import forms
from .models import CustomCrop, Photo, PhotoSize
from .widgets import CustomCropWidget

class CustomCropAdminForm(forms.ModelForm):
    photo = forms.ModelChoiceField(queryset=Photo.objects.all(), required=False)
    photosize = forms.ModelChoiceField(queryset=PhotoSize.objects.all(), required=False)
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomCropAdminForm, self).__init__(*args, **kwargs)
        self.fields['photo'].queryset = Photo.objects.filter(id=self.request.GET['photo_id'])
        self.fields['photo'].queryset = Photo.objects.filter(id=self.request.GET['photo_id'])
        self.fields['photo'].widget=CustomCropWidget(forms.Select(), Photo.objects.get(id=self.request.GET['photo_id']), PhotoSize.objects.get(id=self.request.GET['photosize_id']))
        #self.fields['photo'].widget.attrs['disabled'] = 'disabled'
        self.photo_size = PhotoSize.objects.get(id=self.request.GET['photosize_id'])
        self.fields['photosize'].queryset = PhotoSize.objects.filter(id=self.request.GET['photosize_id'])
        self.fields['photosize'].initial =  self.photo_size
        self.fields['photosize'].widget.attrs['disabled'] = 'disabled'
        self.fields['x'].widget.attrs['readonly'] = 'readonly'
        self.fields['y'].widget.attrs['readonly'] = 'readonly'
        self.fields['width'].widget.attrs['readonly'] = 'readonly'
        self.fields['height'].widget.attrs['readonly'] = 'readonly'
        if CustomCrop.objects.filter(photo__id=self.request.GET['photo_id'], photosize__id=self.request.GET['photosize_id']).count() == 1:
            self.custom_crop = CustomCrop.objects.get(photo__id=self.request.GET['photo_id'], photosize__id=self.request.GET['photosize_id'])
            self.fields['x'].initial = self.custom_crop.x
            self.fields['y'].initial = self.custom_crop.y
            self.fields['width'].initial = self.custom_crop.width
            self.fields['height'].initial = self.custom_crop.height
        else:
            self.fields['width'].initial =  self.photo_size.width
            self.fields['height'].initial =  self.photo_size.height

    def clean_photo(self):
        return Photo.objects.get(id=self.request.GET['photo_id'])
    def clean_photosize(self):
        return PhotoSize.objects.get(id=self.request.GET['photosize_id'])

    class Meta:
        model = CustomCrop