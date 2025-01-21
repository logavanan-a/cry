import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.debug import DjangoDebug
from .models import (WorkState,)

class WorkStateType(DjangoObjectType):
    class Meta:
        model = WorkState

class Query(graphene.ObjectType):
    workstate = graphene.List(WorkStateType)

    def resolve_workstate(self, args, context, info):
        return WorkState.objects.filter(active=2)


schema = graphene.Schema(query=Query)