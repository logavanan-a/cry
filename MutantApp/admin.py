from django.contrib import admin
from mutant.models import ModelDefinition
from mutant.models.field import FieldDefinition
from mutant.contrib.text.models import CharFieldDefinition
from mutant.contrib.numeric.models import BigIntegerFieldDefinition


def register(mdl):

    class MdlAdmin(admin.ModelAdmin):
        list_display = ['__str__'] + [i.name for i in mdl._meta.fields]
        filter_horizontal = [i.name for i in mdl._meta.many_to_many]
    admin.site.register(mdl, MdlAdmin)


for i in ModelDefinition.objects.all():
    mdl = i.model_class()
    register(mdl)



for mdl in [ModelDefinition, FieldDefinition, CharFieldDefinition, BigIntegerFieldDefinition]:
    register(mdl)
