from django.template.defaulttags import register
# imported register


# Register function as template tag
@register.filter
def get_item(dictionary, key):
    # Gets item from dictionary
    return dictionary.get(key)
