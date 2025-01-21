from django.template.defaulttags import register
from survey.models import Question
# Import Prerequisites


# Register function as template tag
@register.filter
def orderq(questions):
    # Questions in order
    return Question.objects.filter(id__in=[i.id for i in questions])
