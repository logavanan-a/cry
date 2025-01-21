from django.forms import ModelForm
from survey.models import *
from django import forms
from django.forms.models import inlineformset_factory

class QuestionForm(forms.ModelForm):
    class Meta:
        model=Question
        fields=['qtype','text','order','code',]
 
class QuestionSecondForm(forms.ModelForm):
    class Meta:
        model=Question
        fields=['validation','qtype','text','order','code',]

class ChoiceForm(forms.ModelForm):
    class Meta:
        model=Choice
        fields=['text','code','order','question']

# ChoiceFormSet = inlineformset_factory(Question, Choice,form=ChoiceForm,extra=5,can_delete=False)

class DataCentreForm(forms.ModelForm):
    class Meta:
        model = DataCentre
        fields = ['name','deo','project','cordinator']
        
#class DataCentreLocationForm(forms.ModelForm):

#    primary_address = forms.CharField(widget=forms.Textarea(attrs={"cols":"20",'rows':"10"}),required=False)
#    class Meta:
#        model = DataCentreLocation
#        fields = ['district','primary_address']
