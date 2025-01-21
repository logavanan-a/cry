from django.http import HttpResponse
from survey.models import Question
from survey.models import Survey, Answer
# Import prerequisites


def report_download(request, id):

    # csv report

    surveyobj = Survey.objects.get(pk=id)
    questions = Question.objects.filter(block__survey=surveyobj).order_by('order')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="qlist-report.csv"'
    writer = csv.writer(response)
    writer.writerow([i.text for i in questions])
    answerobj = Answer.objects.filter(question__block__survey=id)
    ckey = set([i.creation_key for i in answerobj])
    listobj = [Answer.objects.filter(creation_key=i) for i in ckey]
    for i in listobj:
        writer.writerow(i.order_by('question__order'))
    return response
