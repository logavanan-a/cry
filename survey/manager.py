# Model managers for survey models
from masterdata.manager import ActiveQuerySet
from django.contrib.contenttypes.models import ContentType
from django.db import models
# Import prerequisites


class AnswerQuerySet(ActiveQuerySet):

    # Custom queryset for answer model

    @staticmethod
    def processor(var, *args, **kwargs):
        # Processor
        for i in var:
            full_kwargs = kwargs
            full_kwargs.update(i)
            answer.objects.force_create(full_kwargs)

    def force_create(self, **kwargs):
        # Calls force save intead of regular save
        obj = self.model(**kwargs)
        self._for_write = True
        obj.force_save(force_insert=True, using=self.db)
        return obj

    def with_questions(self, *args, **kwargs):
        # Collect answers with questions in json format
        questions = self[0].question.block.survey.questions()
        info = {i.question: i for i in self.filter(*args, **kwargs).prefetch_related('question')}
        missing = [i for i in questions if i not in info]
        for i in missing:
            info[i] = ''
        return info

    def collect_rows(self, party, survey, date, inline=None):

        # Collect answers rowwise
        # Filter anser using given kwargs

        answers = self.filter(
            content_type=ContentType.objects.get_for_model(type(party)),
            object_id=party.id,
            question__block__survey=survey,
            data_level=date,
            inline=inline,
            active=2
        )

        #  Return it as a dict
        return {
            getattr(i.values()[0], 'creation_key', i.values()[0]): i
            for i in [answers.with_questions(creation_key=ans.creation_key)
                      for ans in answers
                      if ans.question == answers[0].question]
        }

    def collect_all_rows(self, location, survey, date, inline=None):
        # Collect all rows in a location
        # If location is a plot, it will give hhs of village instead
        from masterdata.models import Plot
        if survey.del_nicely() == 'Plot':
            parties = Plot.objects.filter(house_hold__village=location)
        else:
            parties = location.contents()
        return {party: self.collect_rows(party, survey, date, inline=None)
                for party in parties}

    def collect_participated_rows(self, *args, **kwargs):
        # Collect rows which participated in a location
        return {a: b for a, b in self.collect_all_rows(*args, **kwargs).items() if b}


class SurveyStatusQuerySet(ActiveQuerySet):

    # Survey Status QuerySet

    def get_fast(survey, location, date=None):

        # Get or create auto handle locations

        return self.get_or_create(
            survey=survey,
            content_type=ContentType.objects.get_for_model(type(location)),
            object_id=location.id,
            date=date,
        )


class KpiReportQuerySet(ActiveQuerySet):

    # Custom queryset for kpi report

    def lev_filter(self, level_obj, *args, **kwargs):
        # evaluate level obj
        fil = super(KpiReportQuerySet, self).filter(*args, **kwargs)
        return fil.filter(level=level_obj.__class__.__name__,
                          level_code=level_obj.id)

    def inlev_filter(self, level_obj, *args, **kwargs):
        # Evaluate Level obj
        # Collect all sublevels
        from partner.models import get_multilevel_children
        return self.filter(id__in=[
            j.id for i in get_multilevel_children(level_obj)
            for j in self.lev_filter(i, *args, **kwargs)
        ])

    def panda_target(self):
        # sum of all targets
        return sum([i.target for i in self])

    def panda_achieved(self):
        # sum of all achieved
        return sum([i.achieved for i in self])
    

class DefaultLanguage(models.QuerySet):

    def get_default_language(self, *args, **kwargs):
        # Returns Language Id
        # Creates a default Language "Englisg" and returns the Language id
        try:
            obj = self.get(name__iexact="English")
        except:
            obj = self.create(name="English", code="ENG")
        return obj

    def active_items(self):
        # Returns active items only
        return self.filter(active=2)

    def get_or_none(self, *args, **kwargs):
        # Returns object and return none if it's not present
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            return None
