# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import copy
from itertools import chain
from datetime import datetime

from django.conf import settings
from django import forms
from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

try:
    from django.forms.widgets import flatatt
except ImportError:
    from django.forms.utils import flatatt

from django.utils.html import format_html
from django.template.loader import render_to_string
from photologue.models import Photo, Gallery, CustomCrop, PhotoSize

class PhotoWidget(forms.Widget):
    def __init__(self, widget, model, image_size):
        #self.is_hidden = widget.is_hidden
        if hasattr(self, 'input_type'):
            self.input_type = 'hidden' if widget.is_hidden else self.input_type
        self.needs_multipart_form = widget.needs_multipart_form
        self.attrs = widget.attrs
        self.choices = widget.choices
        self.widget = widget
        self.model = model
        self.image_size = image_size
        GALLERY_PAGINATE_BY = getattr(settings, 'PHOTOLOGUE_GALLERY_PAGINATE_BY', 20)

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj

    @property
    def media(self):
        return forms.Media(css={'all': ('photologue/css/image-picker.css',)},
                           js=('photologue/js/jquery-1.11.1.min.js', 'photologue/js/image-picker.js',))

    def render(self, name, value, attrs=None, choices=()):
        # try:
        #     name.index("__prefix__")

        #     import string
        #     import random
        #     name = name.replace("__prefix__", "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10)))
        # except ValueError:
        #     pass

        model = self.model
        info = (model._meta.app_label, model._meta.object_name.lower())
        photo_object = None
        if value:
            photo_object = Photo.objects.get(id=value)
            if value not in [val for val, obj in self.choices]:
                choices = ((value, photo_object),)
        self.widget.choices = self.choices
        id = 'id_' + name
        add_image_link = reverse(
            'admin:%s_%s_add'
            % info, current_app=admin.site.name
        )

        # output = [format_html('<div class="image_picker_wrapper"><p class="links"><img src="{5}?{6}" class="selected_image" /><a id="add_{0}" href="{1}?photosize={2}" onclick="return showAddAnotherPopup(this);">{3}</a> <a href="#{0}" onclick="return toggleImagePicker(\'{0}\');">{4}</a></p>',
        #                       id, add_image_link, self.image_size, '+ Añadir imagen nueva', 'Elegir una imagen ya subida', photo_url, datetime.now().time().microsecond)]
        # output.append(format_html('<select data-id="{1}" data-image-size="{2}" data-lookup-path="{3}" data-gallery="-1" data-use-admin-thumbnail="1" data-page="1"{0}>', flatatt(self.build_attrs(attrs, name=name, id=id)), id, self.image_size, reverse('photologue:pl-image-lookup')))
        # options = self.render_options(choices, [value])
        # if options:
        #     output.append(options)
        # output.append('</select>')

        # output.append('<div class="menu"><p id="gallery_{0}">Elegir álbum: '.format(id))
        # output.append('<a id="gallery_{0}_-1" href="#{0}" class="active" onclick="return load_images(\'{0}\', \'gallery\', -1);"><em>(Todas)</em></a> <a id="gallery_{0}_0" href="#{0}" onclick="return load_images(\'{0}\', \'gallery\', 0);"><em>(Sin clasificar)</em></a> '.format(id))
        # for album in Gallery.objects.all():
        #     output.append('<a id="gallery_{0}_{1}" href="#{0}" onclick="return load_images(\'{0}\', \'gallery\', {1});">{2}</a>'.format(id, album.id, album.title))
        # output.append('</p>')
        # cambiar_tamanyo = '<a id="use_admin_thumbnail_' + id + '_%s" href="#' + id + '" onclick="return load_images(\'' + id + '\', \'use-admin-thumbnail\', %s);"%s>%s</a>'
        # output.append('<p id="use_admin_thumbnail_{0}">Tamaño de imagen: {1} {2}</p>'.format(id, cambiar_tamanyo % (1, 1, ' class="active"', 'Icono admin'), cambiar_tamanyo % (0, 0, '', self.image_size)))
        # output.append('<p id="page_{0}" class="pages">Páginas: '.format(id))
        # for page in Paginator(self.choices, 15).page_range:
        #     output.append('<a id="page_{0}_{1}"{2} href="#{0}" onclick="return load_images(\'{0}\', \'page\', {1});">{1}</a>'.format(id, page, ' class="active"' if page==1 else ''))
        # output.append('</p>')
        # output.append('</div></div><script type="text/javascript">$("#id_' + name + '").imagepicker({show_label:true});</script>')
        IMAGE_SIZES = getattr(settings, 'PHOTOLOGUE_IMAGE_SIZES', {})
        im = IMAGE_SIZES.get(self.image_size, ())
        custom_crop_base_url = reverse(
            'admin:%s_%s_add'
            % (self.model._meta.app_label, CustomCrop._meta.model_name), current_app=admin.site.name
        )
        if photo_object:
            custom_crop = ''.join([custom_crop_base_url, '?_to_field=id&_popup=1&photo_id=[PHOTO_ID]&photosize_id=', str(PhotoSize.objects.get(name=self.image_size).id)])
            photo_url = photo_object._get_SIZE_url(self.image_size)
        else:
            custom_crop, photo_url = ''.join([custom_crop_base_url, '?_to_field=id&_popup=1&photo_id=[PHOTO_ID]&photosize_id=', str(PhotoSize.objects.get(name=self.image_size).id)]), ''
        imagesizes = [(im[0], im[1], photo_url, custom_crop, custom_crop.replace('[PHOTO_ID]', str(value)) if value else '')]
        if len(im) > 2:
            for ims in im[2]:
                if ims in IMAGE_SIZES:
                    if photo_object:
                        custom_crop = ''.join([custom_crop_base_url, '?_to_field=id&_popup=1&photo_id=[PHOTO_ID]&photosize_id=', str(PhotoSize.objects.get(name=ims).id)])
                        photo_url = photo_object._get_SIZE_url(ims)
                    else:
                        custom_crop, photo_url = ''.join([custom_crop_base_url, '?_to_field=id&_popup=1&photo_id=[PHOTO_ID]&photosize_id=', str(PhotoSize.objects.get(name=ims).id)]), ''
                    imagesizes.append((ims, IMAGE_SIZES[ims][1], photo_url, custom_crop, custom_crop.replace('[PHOTO_ID]', str(value)) if value else ''))
        return render_to_string('admin/image_picker.html', {
            'galleries': Gallery.objects.all(), 
            'options': self.render_options(choices, [value]), 
            'id': id, 
            'image_sizes': imagesizes, 
            'add_image_link': add_image_link, 
            'select_attrs': flatatt(self.build_attrs(attrs, name=name, id=id)),
            'paginator': Paginator(self.choices, 15),
            'photo_url': photo_url,
        })
        # return mark_safe(''.join(output))

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            selected_choices.remove(option_value)
        else:
            selected_html = ''
        if option_value == '':
            return format_html('<option value="{0}"{1}>{2}</option>',
                               option_value,
                               selected_html,
                               force_text(option_label))
        else:
       #     try:
       #         custom_crop = CustomCrop.objects.get(photo__id=option_value, photosize__name=self.image_size).id
       #     except CustomCrop.DoesNotExist:
       #         custom_crop = 'add'
       #     custom_crop = 'add'
       #     if custom_crop == 'add':
       #     else:
       #         custom_crop = reverse(
       #             'admin:%s_%s_change'
       #             % (self.model._meta.app_label, CustomCrop._meta.model_name), current_app=admin.site.name, args=[custom_crop]
       #         )
            Photo.objects.get(pk=option_value)._get_SIZE_url(self.image_size)
            return format_html('<option data-img-src="{3}" value="{0}"{1}>{2}</option>',
                               option_value,
                               selected_html,
                               force_text(option_label),
                               Photo.objects.get(pk=option_value)._get_SIZE_url('admin_thumbnail'))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(choices, self.choices):
            if len(output) > 15 and force_text(option_value) not in selected_choices:
                continue
            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{0}">', force_text(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return '\n'.join(output)

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(extra_attrs=None, **kwargs)
        return self.attrs

class CustomCropWidget(forms.Widget):
    def __init__(self, widget, photo, photosize):
        self.photo = photo
        self.photosize = photosize
        self.attrs = widget.attrs

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj

    @property
    def media(self):
        return forms.Media(css={'all': ('photologue/css/jquery.Jcrop.min.css', 'photologue/css/custom_crop.css',)},
                           js=('photologue/js/jquery-1.11.1.min.js', 'photologue/js/jquery.Jcrop.js', 'photologue/js/custom_crop.js',))

    def render(self, name, value, attrs=None):
        return mark_safe('<img src="' + self.photo.image.url + '" id="target" data-fixed-ratio="' + ('1' if self.photosize.crop else '0') + '" /><div id="preview-pane"><div class="preview-container"><img src="' + self.photo.image.url + '" class="jcrop-preview"' + (' width="' + str(self.photosize.width) + 'px"' if self.photosize.width > 0 else '') + (' height="' + str(self.photosize.height) + 'px' if self.photosize.height > 0 else '') + '" /></div></div>')
