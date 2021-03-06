import copy
from functools import partial
from django.contrib import admin
from django.db import models
from django.contrib.admin import widgets
#from xadmin.plugins.quickform import RelatedFieldWidgetWrapper as xadminRelatedFieldWidgetWrapper
from .fields import PhotoField, PhotoFormField
from .widgets import PhotoWidget
try:
    import xadmin
    from xadmin.sites import site as xadmin_site
except:
    pass

# autodiscover the admin, very important
admin.autodiscover()
#xadmin.autodiscover()

def __get_model_formfield_for_dbfield(model, inline=None):
    """
    Gets the new formfield_for_dbfield_function for a model
    """
#    if model in admin.site._registry:
    admin_site = admin.site
#    else:
#        admin_site = xadmin_site
    if inline:
        model_admin = inline
    else:
        model_admin = admin_site._registry[model]
    def formfield_for_photo_field(self, db_field, **kwargs):
        """
            (Overrided from BaseModelAdmin to remove the RelatedFieldWidgetWrapper)

            Hook for specifying the form Field instance for a given database Field
            instance.
            If kwargs are given, they're passed to the form Field's constructor.
        """
        # If the field specifies choices, we don't need to look for special
        # admin widgets - we just need to use a select widget of some kind.
        if 'request' in kwargs:
            request = kwargs.pop('request')
        if db_field.choices:
            return self.formfield_for_choice_field(db_field, request, **kwargs)

        # ForeignKey or ManyToManyFields
        if isinstance(db_field, models.ManyToManyField) or isinstance(db_field, models.ForeignKey):
            # Combine the field kwargs with any options for formfield_overrides.
            # Make sure the passed in **kwargs override anything in
            # formfield_overrides because **kwargs is more specific, and should
            # always win.
            if db_field.__class__ in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)

            # Get the correct formfield.
            if isinstance(db_field, models.ForeignKey):
                formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            elif isinstance(db_field, models.ManyToManyField):
                formfield = self.formfield_for_manytomany(db_field, request, **kwargs)

            # For non-raw_id fields, wrap the widget with a wrapper that adds
            # extra HTML -- the "add other" interface -- to the end of the
            # rendered output. formfield can be None if it came from a
            # OneToOneField with parent_link=True or a M2M intermediary.
            if isinstance(db_field, PhotoField):
                pass
            elif formfield and db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(db_field.remote_field.model)
                wrapper_kwargs = {}
                if related_modeladmin:
                    wrapper_kwargs.update(
                        can_add_related=related_modeladmin.has_add_permission(request),
                        can_change_related=related_modeladmin.has_change_permission(request),
                        can_delete_related=related_modeladmin.has_delete_permission(request),
                    )
                formfield.widget = widgets.RelatedFieldWidgetWrapper(
                    formfield.widget, db_field.remote_field, self.admin_site, **wrapper_kwargs
                )

            return formfield

        # If we've got overrides for the formfield defined, use 'em. **kwargs
        # passed to formfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in model_admin.formfield_overrides:
                kwargs = dict(copy.deepcopy(model_admin.formfield_overrides[klass]), **kwargs)
                return db_field.formfield(**kwargs)

        # For any other type of field, just call its formfield() method.
        return db_field.formfield(**kwargs)
    if inline:
        return formfield_for_photo_field
    else:
        return partial(formfield_for_photo_field, model_admin)

def __get_inline_formfield_for_dbfield(inline, field, widget):
    """
    Gets the new formfield_for_dbfield function for an inline
    """
    old_formfield_for_dbfield = inline.formfield_for_dbfield
    def formfield_for_dbfield(db_field, **kwargs):
        if db_field.name == field:
            kwargs['widget'] = widget
        return old_formfield_for_dbfield(db_field, **kwargs)
    return formfield_for_dbfield

def swap_model_field():
    """
    Swaps an admin model field widget (not the inlines where the model is used)
    """
    for model in admin.site._registry:
        admin.site._registry[model].formfield_for_dbfield = __get_model_formfield_for_dbfield(model)
    # try:
    #     if xadmin_site:
    #         if model in xadmin_site._registry:
    #             xadmin_site._registry[model].formfield_for_dbfield = __get_model_formfield_for_dbfield(model)
    # except NameError:
    #     pass
    for registered_model in admin.site._registry:
        if admin.site._registry.has_key(registered_model):
            for inline in admin.site._registry[registered_model].inlines:
                inline.formfield_for_dbfield = __get_model_formfield_for_dbfield(inline.model, inline)
                #inline.formfield_overrides = {PhotoFormField: {'widget': PhotoWidget},}
    #             if inline.model == model:
    #                 inline.formfield_for_dbfield = __get_inline_formfield_for_dbfield(inline, inline.model.field, inline.model.widget)
                #inline.formfield_for_dbfield = __get_model_formfield_for_dbfield(inline.model)