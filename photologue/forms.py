# -*- coding: utf-8 -*-
from django import forms
from .models import CustomCrop, Photo, PhotoSize, Gallery
from .widgets import CustomCropWidget
from django.conf import settings

MULTISITE = getattr(settings, 'PHOTOLOGUE_MULTISITE', False)
ENABLE_TAGS = getattr(settings, 'PHOTOLOGUE_ENABLE_TAGS', False)

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
        fields = "__all__"


class PhotoAdminForm(forms.ModelForm):
    add_to_gallery = forms.ModelChoiceField(queryset=Gallery.objects.all(), required=False, label='Añadir al álbum')

    def __init__(self, *args, **kwargs):
        if hasattr(self, 'request'):
            request = self.request
            super(PhotoAdminForm, self).__init__(*args, **kwargs)
            if '_add_to_gallery' in request.GET:
                self.fields['add_to_gallery'].initial = request.GET.get('_add_to_gallery')
        else:
            super(PhotoAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Photo

        if MULTISITE:
            exclude = []
        else:
            exclude = ['sites']
        if not ENABLE_TAGS:
            exclude.append('tags')