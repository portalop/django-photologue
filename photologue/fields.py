from django.db import models
from django import forms
from photologue.models import Photo
from widgets import PhotoWidget
#from south.modelsinspector import add_introspection_rules

#add_introspection_rules([], ["^photologue\.fields\.PhotoField"])

class PhotoFormField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.image_size = kwargs.pop('image_size', 'thumbnail')
        self.widget = PhotoWidget(forms.Select(), Photo, self.image_size)
        self.widget.can_add_related = False
        super(PhotoFormField, self).__init__(*args, **kwargs)
        #photo_ids = [photo.id for photo in Photo.objects.all().order_by('-date_added')[:15]]
        #photo_ids.append(self.initial)
        #self.queryset = Photo.objects.filter(id__in=photo_ids)

class PhotoField(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.image_size = kwargs.pop('image_size', 'thumbnail')
        kwargs.setdefault('to', 'photologue.Photo')
        super(PhotoField, self).__init__(*args, **kwargs)
    def formfield(self, **kwargs):
        defaults = {'form_class': PhotoFormField, 'image_size': self.image_size}
        defaults.update(kwargs)
        return super(PhotoField, self).formfield(**defaults)
    def deconstruct(self):
        name, path, args, kwargs = super(PhotoField, self).deconstruct()
        # Only include kwarg if it's not the default
        if self.image_size != "thumbnail":
            kwargs['image_size'] = self.image_size
        return name, path, args, kwargs