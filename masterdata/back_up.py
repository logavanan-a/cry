class StateDetail(RetrieveUpdateDestroyAPIView):
    """State Basic Operations."""

    queryset = Boundary.objects.filter(active=2)
    serializer_class = BoundarySerializer


class StateDetail(APIView):
    """State Basic Operations."""

    queryset = Boundary.objects.filter(boundary_level=3, active=2)
    serializer_class = BoundarySerializer


class TalukCreate(ListCreateAPIView):
    """Taluk Create and listing."""

    queryset = Boundary.objects.filter(boundary_level=4, active=2)
    serializer_class = BoundarySerializer


class TalukDetail(RetrieveUpdateDestroyAPIView):
    """Taluk Basic Operations."""

    queryset = Boundary.objects.filter(boundary_level=4, active=2)
    serializer_class = BoundarySerializer


class GramaPanchayatCreate(ListCreateAPIView):
    """GramaPanchyat Create and listing."""

    queryset = Boundary.objects.filter(boundary_level=5, active=2)
    serializer_class = BoundarySerializer


class GramaPanchayat(RetrieveUpdateDestroyAPIView):
    """GramaPanchyat Basic Operations."""

    queryset = Boundary.objects.filter(boundary_level=5, active=2)
    serializer_class = BoundarySerializer


class MandalCreate(ListCreateAPIView):
    """Mandal Create and listing."""

    queryset = Boundary.objects.filter(boundary_level=6, active=2)
    serializer_class = BoundarySerializer


class MandalDetail(RetrieveUpdateDestroyAPIView):
    """Mandal Basic Operations."""

    queryset = Boundary.objects.filter(boundary_level=6, active=2)
    serializer_class = BoundarySerializer


class VillageCreate(ListCreateAPIView):
    """Village Create and listing."""

    queryset = Boundary.objects.filter(boundary_level=7, active=2)
    serializer_class = BoundarySerializer


class VillageDetail(RetrieveUpdateDestroyAPIView):
    """Village Basic Operations."""

    queryset = Boundary.objects.filter(boundary_level=7, active=2)
    serializer_class = BoundarySerializer


class MandalCreate(APIView):
    """Mandal Create."""

    def post(self, request):
        """To Create Mandal."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class MandalListing(APIView):
    """Mandal Listing."""

    def post(self, request):
        """To Get Mandal List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '5':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class MandalDetial(APIView):
    """Mandal Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '5':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class MandalUpdate(APIView):
    """
    API to update the Mandal.
    """

    def post(self, request):
        """To Create Mandal.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class MandalAction(APIView):
    """
    API to update the Mandal.
    """

    def post(self, request):
        """To Create District.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}
        else:
            pass
        return Response(response)


class VillageHabitationCreate(APIView):
    """Village Habitation Create."""

    def post(self, request):
        """To Create Village Habitation."""
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundarySerializer(data=data)
        try:
            if serializer.is_valid():
                r = requests.post(
                    HOST_URL + '/masterdata/boundary/', data=data)
                response = {'status': r.status_code,
                            'message': 'Successfully created', 'data': data}
            else:
                response.update(erros=serializer.errors)
        except:
            pass
        return Response(response)


class VillageHabitationListing(APIView):
    """Village Habitation Listing."""

    def post(self, request):
        """To Get Village Habitation List."""
        data = request.data
        map_data = {'key': 1, 'level': data.get('level')}
        response = {'status': 'Something went Wrong', 'data': data}
        serializer = BoundaryListingSerializer(data=data)
        if serializer.is_valid() and data.get('level') == '8':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/list/', data=map_data)
            get_loc_list = literal_eval(ru.content)
            get_page = int(get_loc_list[-1].get('pages'))
            del get_loc_list[-1]
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': get_loc_list}
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(
                response.get('data'), request)
            return paginator.get_paginated_response(result_page, response.get('status'), response.get('message'), int(map_data.get('level')),  get_page)
        else:
            response.update(erros=serializer.errors, level='Level is wrong.')
        return Response(response)


class VillageHabitationDetial(APIView):
    """Village Habitation Detail View."""

    def post(self, request):
        """
        API to get pk value.
        ---
        parameters:
        - name: pk
          description: pass pk
          required: true
          type: integer
          paramType: form
        - name: level
          description: pass level
          required: true
          type: integer
          paramType: form
        """
        map_data = {'pk': request.data.get('pk')}
        response = {'status': 'Something went Wrong', 'data': map_data}
        if map_data.get('pk') and request.data.get('level') == '8':
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/detail/', data=map_data)
            response = {'status': ru.status_code,
                        'message': 'Successfully Retrieved', 'data': json.loads(ru.content)}
        else:
            response.update({'message': 'level is wrong.'})
        return Response(response)


class VillageHabitationUpdate(APIView):
    """
    API to update the Village Habitation.
    """

    def post(self, request):
        """To Create Village Habitation.
        """
        data = request.data
        ru = requests.post(
            HOST_URL + '/masterdata/boundary/update/', data=data)
        response = {'status': ru.status_code,
                    'message': literal_eval(ru.content)}
        return Response(response)


class VillageHabitationAction(APIView):
    """
    API to update the Village Habitation.
    """

    def post(self, request):
        """To Create Village Habitation.
        ---
        parameters:
        - name: object_id
          description: pass object_id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        response = {'status': 'Something went Wrong', 'data': data}
        if data:
            ru = requests.post(
                HOST_URL + '/masterdata/boundary/actions/', data=data)
            response = {'status': ru.status_code,
                        'data': json.loads(ru.content)}
        else:
            pass
        return Response(response)

    url(r'^mandal/create/$', MandalCreate.as_view()),
    url(r'^mandal/listing/$', MandalListing.as_view()),
    url(r'^mandal/detail/$', MandalDetial.as_view()),
    url(r'^mandal/update/$', MandalUpdate.as_view()),
    url(r'^mandal/action/$', MandalAction.as_view()),
    url(r'^habitation/village/create/$', VillageHabitationCreate.as_view()),
    url(r'^habitation/village/listing/$', VillageHabitationListing.as_view()),
    url(r'^habitation/village/detail/$', VillageHabitationDetial.as_view()),
    url(r'^habitation/village/update/$', VillageHabitationUpdate.as_view()),
    url(r'^habitation/village/action/$', VillageHabitationAction.as_view()),


def get_levels_upper_data(child_id, upper_level):
    wanted_level = upper_level
    all_location = Boundary.objects.filter(active=2)
    all_levels = {}
    if wanted_level > 7:
        print('Level is Incorrect!')
    else:
        par_level, get_parent = Boundary.objects.filter(
            id=child_id).values_list('boundary_level', 'parent_id')[0]
        level = par_level - 1
        list_parent = [get_parent]
        all_levels[level] = list_parent
        while level > wanted_level:
            loc = all_levels.get(level)
            get_location = all_location.filter(
                id__in=loc, boundary_level=level).values_list('parent__id', flat=True)
            level -= 1
            all_levels[level] = get_location
    return all_levels.get(wanted_level)


level_2 = ['parent.id', 'parent.name',
           'parent.boundary_level', 'id', 'name', 'boundary_level']
level_3 = ['parent.parent.id', 'parent.parent.name', 'parent.parent.boundary_level',
           'parent.id', 'parent.name', 'parent.boundary_level', 'id', 'name', 'boundary_level']
level_4 = ['parent.parent.parent.id', 'parent.parent.parent.name', 'parent.parent.parent.boundary_level',
           'parent.parent.id', 'parent.parent.name', 'parent.parent.boundary_level',
           'parent.id', 'parent.name', 'parent.boundary_level', 'id', 'name', 'boundary_level']
level_5 = ['parent.parent.parent.parent.id', 'parent.parent.parent.parent.name',
           'parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.id', 'parent.parent.parent.name', 'parent.parent.parent.boundary_level',
           'parent.parent.id', 'parent.parent.name', 'parent.parent.boundary_level',
           'parent.id', 'parent.name', 'parent.boundary_level', 'id', 'name', 'boundary_level']
level_6 = ['parent.parent.parent.parent.parent.id', 'parent.parent.parent.parent.parent.name',
           'parent.parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.parent.id', 'parent.parent.parent.parent.name',
           'parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.id', 'parent.parent.parent.name', 'parent.parent.parent.boundary_level',
           'parent.parent.id', 'parent.parent.name', 'parent.parent.boundary_level',
           'parent.id', 'parent.name', 'parent.boundary_level', 'id', 'name', 'boundary_level']
level_7 = ['parent.parent.parent.parent.parent.parent.id', 'parent.parent.parent.parent.parent.parent.name',
           'parent.parent.parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.parent.parent.id', 'parent.parent.parent.parent.parent.name',
           'parent.parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.parent.id', 'parent.parent.parent.parent.name',
           'parent.parent.parent.parent.boundary_level',
           'parent.parent.parent.id', 'parent.parent.parent.name', 'parent.parent.parent.boundary_level',
           'parent.parent.id', 'parent.parent.name', 'parent.parent.boundary_level',
           'parent.id', 'parent.name', 'parent.boundary_level', 'id', 'name', 'boundary_level']
