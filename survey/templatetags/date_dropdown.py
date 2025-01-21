# template tags for piriodic surveys
from django.template.defaulttags import register
from survey.models import Answer
import datetime as d
# Import prerequisites


def find_dropdown_choices(question):

    # Find the dropdown choices

    per = int(question.block.survey.piriodicity)
    today = d.datetime.today()
    strf = d.datetime.strftime
    delta = d.timedelta
    fortdict = {True: 'First', False: 'Last'}
    quatdict = {1: 'MQ - First', 2: 'MQ - First', 3: 'MQ - First',
                4: 'JQ - Second', 5: 'JQ - Second', 6: 'JQ - Second',
                7: 'SQ - Third', 8: 'SQ - Third', 9: 'SQ - Third',
                10: 'DQ - Fourth', 11: 'DQ - Fourth', 12: 'DQ - Fourth', }

    if per == 1:
        # Daily
        return [strf(that_day, '%b-%d')
                for that_day in [today+delta(i) for i in range(-45, 0)]]

    elif per == 2:
        # Weekly
        return [strf(that_day, '%b-%d') + ' to ' + strf(that_day+delta(6), '%b-%d')
                for that_day in [today+delta(i)+delta(int(strf(today, '%w'))) for i in range(-60, 0, 7)]]

    elif per == 3:
        # Fortnightly
        return [strf(that_day, '%s %s %s Half' % ('%B', '%Y', fortdict[that_day.day<15]))
                for that_day in [today+delta(i) for i in range(-365, 0, 15)]]

    elif per == 4:
        # Monthly
        return [strf(that_day, '%B %Y')
                for that_day in [today+delta(i) for i in range(-365, 0, 30)]]

    elif per == 5:
        # Quatdict
        return [strf(that_day, '%s %s Quater' % ('%Y', quatdict[that_day.month]))
                for that_day in [today+delta(i) for i in range(-365, 0, 92)]]


# Register function as template tag
@register.filter
def load_date_dropdown(question, row):

    # Returns date dropdown html str

    if question.block.survey.piriodicity == '0':
        answers = Answer.objects.filter(creation_key=row, text='Name')
        value = answers[0].text if answers else ''
        return '<input type="text" name="{question_id}-{row}" id="{question_id}" value="{inline}">'.format(
            question_id=question.id, row=row, inline=value,
        )
        
    answers = Answer.objects.filter(creation_key=row, question__text='Date')
    dates = find_dropdown_choices(question)

    per = int(question.block.survey.piriodicity)

    if per == 1:
        return '''
        <input type="text" name="{question_id}-{row}" class="datepicker-past" readonly="readonly" id="{question_id}|{row}" value={val}>
        '''.format(
            question_id=question.id, row=row, val=answers.get_or_none() or '',
        )

    options = ''.join([
        '<option value="%s"%s>%s</option>' % (i, 'selected' if str(i) in [j.text for j in answers] else '', i)
        for i in dates])

    return '''
    <select name="{question_id}-{row}">
    <option value="">-----------</option>{options}
    </select> '''.format(
        question_id=question.id, row=row, options=options,
    )
