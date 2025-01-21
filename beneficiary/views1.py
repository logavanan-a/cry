from beneficiary.views import *

class RetreiveLiveParentsListing(APIView):

    def get(self, request, *args, **kwargs):
        """
            Retreive Beneficiary based on name search
            ---
            parameters:
            - name: beneficiary_type_id
              description: pass beneficiary type id
              required: true
              type: integer
              paramType: form
            - name: user_name
              description: pass username
              required: false
              type: string
              paramType: form
            - name: partner_id
              description: pass partner id
              required: true
              type: integer
              paramType: form
        """
        data = request.query_params
        btid = data.get('beneficiary_type_id', None)
        partner_id = data.get('partner_id', None)
        user_name = data.get('user_name', None)
        parent_obj = None
        beneficiary_list = []
        try:
            parent_obj = BeneficiaryType.objects.get(id=btid, is_main=0).parent
        except:
            pass
        if parent_obj:
            beneficiary_type_objs = BeneficiaryType.objects.filter(parent=\
                        parent_obj, is_main=2)
            for i in beneficiary_type_objs:
                beneficiary_obj = Beneficiary.objects.filter(beneficiary_type=i,\
                         active=2, partner_id=partner_id)
                if user_name:
                    beneficiary_obj = beneficiary_obj.filter(name__icontains=\
                                user_name
                                )
                for j in beneficiary_obj:
                    beneficiary_dict = {}
                    beneficiary_dict.update({'id':j.id, 'name':j.name})
                    beneficiary_list.append(beneficiary_dict)
        return Response(beneficiary_list)

class HouseholdMotherListing(APIView):
    def get(self,request,*args,**kwargs):
        """
            Retreive Beneficiary based on name search
            ---
            parameters:
            - name: hh_id
              description: pass household id
              required: true
              type: integer
              paramType: form
        """
        household_id = request.query_params.get('hh_id')
        mother_list = Beneficiary.objects.filter(active=2,beneficiary_type__id=3,
                      parent_id=household_id).values('uuid','name')
        return Response({'status':2,'mother_list':mother_list})
        

