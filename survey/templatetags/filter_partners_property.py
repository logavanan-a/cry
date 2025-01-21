from django.template.defaulttags import register
from common_methods import *
#Import Prerequisites


# Register function as template tag
@register.filter
def filter_partners_property(queryset):
    # Filter surveys of a partner
    if queryset.model.__name__ == 'Survey':
        return queryset.filter(project__program__partner__code=sub_domain())
