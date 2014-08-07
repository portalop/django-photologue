# -*- encoding: utf-8 -*-

from django.conf import settings
from django.views.generic.dates import ArchiveIndexView, DateDetailView, DayArchiveView, MonthArchiveView, YearArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import View
from .models import Photo, Gallery, PhotoSize, CustomCrop
import json
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.contrib import admin
from django.core.urlresolvers import reverse

# Number of galleries to display per page.
GALLERY_PAGINATE_BY = getattr(settings, 'PHOTOLOGUE_GALLERY_PAGINATE_BY', 20)

if GALLERY_PAGINATE_BY != 20:
    import warnings
    warnings.warn(
        DeprecationWarning('PHOTOLOGUE_GALLERY_PAGINATE_BY setting will be removed in Photologue 3.0'))

# Number of photos to display per page.
PHOTO_PAGINATE_BY = getattr(settings, 'PHOTOLOGUE_PHOTO_PAGINATE_BY', 20)

if PHOTO_PAGINATE_BY != 20:
    import warnings
    warnings.warn(
        DeprecationWarning('PHOTOLOGUE_PHOTO_PAGINATE_BY setting will be removed in Photologue 3.0'))

# Gallery views.


class GalleryListView(ListView):
    queryset = Gallery.objects.on_site().is_public()
    paginate_by = GALLERY_PAGINATE_BY


class GalleryDetailView(DetailView):
    queryset = Gallery.objects.on_site().is_public()


class GalleryDateView(object):
    queryset = Gallery.objects.on_site().is_public()
    date_field = 'date_added'
    allow_empty = True


class GalleryDateDetailView(GalleryDateView, DateDetailView):
    pass


class GalleryArchiveIndexView(GalleryDateView, ArchiveIndexView):
    pass


class GalleryDayArchiveView(GalleryDateView, DayArchiveView):
    pass


class GalleryMonthArchiveView(GalleryDateView, MonthArchiveView):
    pass


class GalleryYearArchiveView(GalleryDateView, YearArchiveView):
    pass

# Photo views.


class PhotoListView(ListView):
    queryset = Photo.objects.on_site().is_public()
    paginate_by = PHOTO_PAGINATE_BY


class PhotoDetailView(DetailView):
    queryset = Photo.objects.on_site().is_public()


class PhotoDateView(object):
    queryset = Photo.objects.on_site().is_public()
    date_field = 'date_added'
    allow_empty = True


class PhotoDateDetailView(PhotoDateView, DateDetailView):
    pass


class PhotoArchiveIndexView(PhotoDateView, ArchiveIndexView):
    pass


class PhotoDayArchiveView(PhotoDateView, DayArchiveView):
    pass


class PhotoMonthArchiveView(PhotoDateView, MonthArchiveView):
    pass


class PhotoYearArchiveView(PhotoDateView, YearArchiveView):
    pass

class ImageLookupView(View):
    def get(self, *args, **kwargs):
        options = []
        custom_crop = reverse(
            'admin:%s_%s_add'
            % (CustomCrop._meta.app_label, CustomCrop._meta.model_name), current_app=admin.site.name
        )
        for photo in Photo.objects.all().exclude(id__in=self.request.GET["exclude_ids"].split(","))[:15]:
            options.append(format_html('<option data-img-src="{1}" data-crop-url="{2}" value="{0}">',
                                        photo.id,
                                        photo._get_SIZE_url(self.request.GET["image_size"]),
                                        ''.join([custom_crop, '?photo_id=', str(photo.id), '&photosize_id=', str(PhotoSize.objects.get(name=self.request.GET["image_size"]).id)])) + unicode(photo) + '</option>')
        resp = {'new_options': ''.join(options),}
        return HttpResponse(json.dumps(resp), mimetype="application/json" )
