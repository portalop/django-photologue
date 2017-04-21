from django import forms
from django.forms import ModelForm
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.views.main import TO_FIELD_VAR
from django.contrib.sites.models import Site
from django.contrib import messages
from django.template.response import SimpleTemplateResponse
from django.core.urlresolvers import reverse
from django.utils.html import escape, escapejs
from django.utils.encoding import force_text
from django.utils.translation import ungettext, ugettext_lazy as _

from .models import Gallery, Photo, GalleryUpload, PhotoEffect, PhotoSize, \
    Watermark, CustomCrop
from .forms import CustomCropAdminForm, PhotoAdminForm
import adminwidgetswap

MULTISITE = getattr(settings, 'PHOTOLOGUE_MULTISITE', False)

ENABLE_TAGS = getattr(settings, 'PHOTOLOGUE_ENABLE_TAGS', False)


class GalleryAdminForm(forms.ModelForm):

    class Meta:
        model = Gallery
        if MULTISITE:
            exclude = []
        else:
            exclude = ['sites']
        if not ENABLE_TAGS:
            exclude.append('tags')


class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_added', 'photo_count', 'is_public')
    list_filter = ['date_added', 'is_public']
    if MULTISITE:
        list_filter.append('sites')
    date_hierarchy = 'date_added'
    prepopulated_fields = {'slug': ('title',)}
    form = GalleryAdminForm
    if MULTISITE:
        filter_horizontal = ['sites']
    if MULTISITE:
        actions = [
            'add_to_current_site',
            'add_photos_to_current_site',
            'remove_from_current_site',
            'remove_photos_from_current_site'
        ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ Set the current site as initial value. """
        if db_field.name == "sites":
            kwargs["initial"] = [Site.objects.get_current()]
        return super(GalleryAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def save_related(self, request, form, *args, **kwargs):
        """
        If the user has saved a gallery with a photo that belongs only to
        different Sites - it might cause much confusion. So let them know.
        """
        super(GalleryAdmin, self).save_related(request, form, *args, **kwargs)
        orphaned_photos = form.instance.orphaned_photos()
        if orphaned_photos:
            msg = ungettext(
                'The following photo does not belong to the same site(s)'
                ' as the gallery, so will never be displayed: %(photo_list)s.',
                'The following photos do not belong to the same site(s)'
                ' as the gallery, so will never be displayed: %(photo_list)s.',
                len(orphaned_photos)
            ) % {'photo_list': ", ".join([photo.title for photo in orphaned_photos])}
            messages.warning(request, msg)

    def add_to_current_site(modeladmin, request, queryset):
        current_site = Site.objects.get_current()
        current_site.gallery_set.add(*queryset)
        msg = ungettext(
            "The gallery has been successfully added to %(site)s",
            "The galleries have been successfully added to %(site)s",
            len(queryset)
        ) % {'site': current_site.name}
        messages.success(request, msg)

    add_to_current_site.short_description = \
        _("Add selected galleries from the current site")

    def remove_from_current_site(modeladmin, request, queryset):
        current_site = Site.objects.get_current()
        current_site.gallery_set.remove(*queryset)
        msg = ungettext(
            "The gallery has been successfully removed from %(site)s",
            "The selected galleries have been successfully removed from %(site)s",
            len(queryset)
        ) % {'site': current_site.name}
        messages.success(request, msg)

    remove_from_current_site.short_description = \
        _("Remove selected galleries from the current site")

    def add_photos_to_current_site(modeladmin, request, queryset):
        photos = Photo.objects.filter(galleries__in=queryset)
        current_site = Site.objects.get_current()
        current_site.photo_set.add(*photos)
        msg = ungettext(
            'All photos in gallery %(galleries)s have been successfully added to %(site)s',
            'All photos in galleries %(galleries)s have been successfully added to %(site)s',
            len(queryset)
        ) % {
            'site': current_site.name,
            'galleries': ", ".join(["'{0}'".format(gallery.title)
                                    for gallery in queryset])
        }
        messages.success(request, msg)

    add_photos_to_current_site.short_description = \
        _("Add all photos of selected galleries to the current site")

    def remove_photos_from_current_site(modeladmin, request, queryset):
        photos = Photo.objects.filter(galleries__in=queryset)
        current_site = Site.objects.get_current()
        current_site.photo_set.remove(*photos)
        msg = ungettext(
            'All photos in gallery %(galleries)s have been successfully removed from %(site)s',
            'All photos in galleries %(galleries)s have been successfully removed from %(site)s',
            len(queryset)
        ) % {
            'site': current_site.name,
            'galleries': ", ".join(["'{0}'".format(gallery.title)
                                    for gallery in queryset])
        }
        messages.success(request, msg)

    remove_photos_from_current_site.short_description = \
        _("Remove all photos in selected galleries from the current site")

admin.site.register(Gallery, GalleryAdmin)


class GalleryUploadAdmin(admin.ModelAdmin):

    def has_change_permission(self, request, obj=None):
        return False  # To remove the 'Save and continue editing' button

    def save_model(self, request, obj, form, change):
        # Warning the user when things go wrong in a zip upload.
        obj.request = request
        obj.save()

admin.site.register(GalleryUpload, GalleryUploadAdmin)


class PhotoAdmin(admin.ModelAdmin):
    if ENABLE_TAGS:
        list_display = ('title', 'date_taken', 'date_added',
                        'is_public', 'tags', 'view_count', 'admin_thumbnail')
    else:
        list_display = ('title', 'date_taken', 'date_added',
                        'is_public', 'view_count', 'admin_thumbnail')
    list_filter = ['date_added', 'is_public']
    if MULTISITE:
        list_filter.append('sites')
    search_fields = ['title', 'slug', 'caption']
    list_per_page = 10
    prepopulated_fields = {'slug': ('title',)}
    form = PhotoAdminForm
    if MULTISITE:
        filter_horizontal = ['sites']
    if MULTISITE:
        actions = ['add_photos_to_current_site', 'remove_photos_from_current_site']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ Set the current site as initial value. """
        if db_field.name == "sites":
            kwargs["initial"] = [Site.objects.get_current()]
        return super(PhotoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def add_photos_to_current_site(self, request, queryset):
        current_site = Site.objects.get_current()
        current_site.photo_set.add(*queryset)
        msg = ungettext(
            'The photo has been successfully added to %(site)s',
            'The selected photos have been successfully added to %(site)s',
            len(queryset)
        ) % {'site': current_site.name}
        messages.success(request, msg)

    add_photos_to_current_site.short_description = \
        _("Add selected photos to the current site")

    def remove_photos_from_current_site(self, request, queryset):
        current_site = Site.objects.get_current()
        current_site.photo_set.remove(*queryset)
        msg = ungettext(
            'The photo has been successfully removed from %(site)s',
            'The selected photos have been successfully removed from %(site)s',
            len(queryset)
        ) % {'site': current_site.name}
        messages.success(request, msg)

    remove_photos_from_current_site.short_description = \
        _("Remove selected photos from the current site")

    def response_add(self, request, obj, post_url_continue=None):
        pk_value = obj._get_pk_val()

        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            custom_crop = reverse(
                'admin:%s_%s_add'
                % (self.model._meta.app_label, CustomCrop._meta.model_name), current_app=admin.site.name
            )
            parametros = {
                'pk_value': escape(pk_value), # for possible backwards-compatibility
                'value': escape(value),
                'obj': escapejs(obj)
            }
            if request.GET.get('photosize'):
                parametros.update({
                    'photo_url': escape(obj._get_SIZE_url(request.GET.get('photosize'))),
                    'crop_url': ''.join([custom_crop, '?photo_id=', escape(value), '&photosize_id=', str(PhotoSize.objects.get(name=request.GET.get('photosize')).id)])
                })
            return SimpleTemplateResponse('admin/photopicker_popup_response.html', parametros)
        return super(PhotoAdmin, self).response_add(request, obj, post_url_continue)

    def save_model(self, request, obj, form, change):
        obj.save()
        gallery_obj = form.cleaned_data.get('add_to_gallery')
        if gallery_obj:
            gallery_obj.photos.add(obj)
            gallery_obj.save()

    def get_form(self, request, obj=None, **kwargs):
        a = super(PhotoAdmin, self).get_form(request, obj, **kwargs)
        a.request = request
        return a

admin.site.register(Photo, PhotoAdmin)

class PhotoEffectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color', 'brightness',
                    'contrast', 'sharpness', 'filters', 'admin_sample')
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Adjustments', {
            'fields': ('color', 'brightness', 'contrast', 'sharpness')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('Reflection', {
            'fields': ('reflection_size', 'reflection_strength', 'background_color')
        }),
        ('Transpose', {
            'fields': ('transpose_method',)
        }),
    )

admin.site.register(PhotoEffect, PhotoEffectAdmin)


class PhotoSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'width', 'height', 'crop', 'pre_cache', 'effect', 'increment_count')
    fieldsets = (
        (None, {
            'fields': ('name', 'width', 'height', 'quality')
        }),
        ('Options', {
            'fields': ('upscale', 'crop', 'pre_cache', 'increment_count')
        }),
        ('Enhancements', {
            'fields': ('effect', 'watermark',)
        }),
    )

admin.site.register(PhotoSize, PhotoSizeAdmin)


class WatermarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'opacity', 'style')

admin.site.register(Watermark, WatermarkAdmin)

class CustomCropAdmin(admin.ModelAdmin):
    form = CustomCropAdminForm
    fields = ('photo', 'photosize', 'x', 'y', 'width', 'height')
    def save_model(self, request, obj, form, change):
        if not change:
            if CustomCrop.objects.filter(photo=obj.photo, photosize=obj.photosize).count() > 0:
                old_crop = CustomCrop.objects.get(photo=obj.photo, photosize=obj.photosize)
                old_crop.x = obj.x
                old_crop.y = obj.y
                old_crop.width = obj.width
                old_crop.height = obj.height
                obj = old_crop
        obj.save()
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(CustomCropAdmin, self).get_form(request, obj, **kwargs)
        class ModelFormMetaClass(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return AdminForm(*args, **kwargs)
        return ModelFormMetaClass

    def response_add(self, request, obj, post_url_continue=None):
        pk_value = obj._get_pk_val()
        if IS_POPUP_VAR in request.POST:
            return SimpleTemplateResponse('admin/photopicker_popup_response.html', {
                'pk_value': escape(pk_value),  # for possible backwards-compatibility
                'value': '',
                'obj': escapejs(obj),
                'photo_url': escape(obj.photo._get_SIZE_url(obj.photosize.name))
            })
        return super(CustomCropAdmin, self).response_add(request, obj, post_url_continue)


admin.site.register(CustomCrop, CustomCropAdmin)