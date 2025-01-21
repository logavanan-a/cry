class GetStates(CreateAPIView):
    queryset = WorkFlowComment.objects.filter(active=2).order_by('-id')
    serializer_class = WorkFlowGetStates

    def create(self, request, *args, **kwargs):
        response = {'status': 0, 'message': 'Something went wrong.'}
        data = Box(request.data)
        serializer = self.get_serializer(data=data.to_dict())
        if serializer.is_valid():
            get_batch = self.get_queryset().filter(
                batch__id=data.batch_id, curr_state__id=data.curr_state)
            response = {'status': 2,
                        'message': 'Successfully retrieved the list.'}
            response['comment'] = [{'id': c.id, 'remarks': c.remarks or '',
                                    'comment_by': c.comment_by.username if c.comment_by else ''}
                                   for c in get_batch]
        else:
            response.update(unpack_errors(serializer.errors))
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_users_work_state(self):
        get_users = {fs.id: {'state': fs.workstate.name, 'users': [usr.id for usr in fs.users.filter(
            is_active=2)]} for fs in self.flow_state.filter(active=2)}
        return get_users


def www():
    of = open('xxx.csv', 'w')
    writer = csv.writer(of)
    ques = Question.objects.all()
    writer.writerow([q.name for q in ques])
    al = []
    for qs in ques:
        aa = []
        if qs.type_text == 'T':
            ans = Answer.objects.filter(question=qs)
            aa.append(ans[0].text if ans else '')
        else:
            ans = ','.join(Answer.objects.filter(
                question=qs).values('choice__name', flat=True))
            aa.append(ans)
        al.append(aa)
    for x in al:
        writer.writerow(x)


class WorkFlowCommentView(ListCreateAPIView):
    queryset = WorkFlowComment.objects.filter(active=2)
    serializer_class = WorkFlowCommentSerializer
    serializer_class_secondary = CommentSerializer

    def perform_create(self, serializer, serializer_child, data):
        new_data = data
        types = new_data.pop('types')
        comment = new_data.pop('comment')
        status = new_data.pop('status')
        curr_user = new_data.pop('curr_user')
        previous_tag_user = new_data.pop('previous_tag_user')
        next_tag_user = new_data.pop('next_tag_user')
        previour_state = new_data.pop('previour_state')
        next_state = new_data.pop('next_state')
        batch = WorkFlowBatch.objects.get(id=new_data.get('batch'))
        curr_state = WorkStateUserRelation.objects.get(
            id=new_data.get('curr_state'))
        prime, created = WorkFlowComment.objects.get_or_create(
            batch=batch, curr_state=curr_state)
        get_previous_states = batch.current_status.workflow.get_previous_state_values()
        get_next_states = batch.current_status.workflow.get_next_level_value()
        prime.status = types
        prime.curr_user_id = curr_user
        if next_tag_user != '0':
            prime.next_tag_user_id = next_tag_user
        if not prime.previous_tag_user_id:
            if previous_tag_user != '0':
                prime.previous_tag_user_id = previous_tag_user
        if get_previous_states.get(curr_state.id):
            prime.previour_state_id = get_previous_states.get(curr_state.id)
        if get_next_states.get(curr_state.id):
            prime.next_state_id = get_next_states.get(curr_state.id)
        prime.save()
        second = Comment.objects.create(curr_state=curr_state)
        second.comment = comment
        second.workflow_cmt = prime
        second.status = types
        second.curr_user_id = curr_user
        if next_tag_user != '0':
            second.next_tag_user_id = next_tag_user
        if previous_tag_user != '0':
            second.previous_tag_user_id = previous_tag_user
        if get_previous_states.get(curr_state.id):
            second.previour_state_id = get_previous_states.get(curr_state.id)
        if get_next_states.get(curr_state.id):
            prime.next_state_id = get_next_states.get(curr_state.id)
        if data.get('commented_by') != '0':
            second.commented_by_id = int(data.get('commented_by'))
        if data.get('commented_to') != '0':
            second.commented_to_id = int(data.get('commented_to'))
        second.save()
        return prime, second


if data.previour_state != '0':
                get_first = get_first.filter(
                    previour_state__id=data.previour_state)
            get_second = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.curr_user,
                curr_state__id=data.curr_state_id).order_by('-id')
            if data.previous_user != '0':
                get_second = get_second.filter(
                    commented_to__id=data.previous_user)
            if data.previour_state != '0':
                get_second = get_second.filter(
                    previour_state__id=data.previour_state)
            get_third = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.previous_user,
                curr_state__id=data.curr_state_id,
                commented_to__id=data.curr_user).order_by('-id')
            get_fourth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_by__id=data.curr_user,
                previour_state__id=data.curr_state_id).order_by('-id')
            get_fifth = self.get_queryset().filter(
                workflow_cmt__batch__id=data.batch_id,
                commented_to__id=data.curr_user,
                curr_state__id=data.curr_state_id).order_by('-id')
            if data.next_state != '0':
                get_fifth = get_fifth.filter(
                    workflow_cmt__next_state__id=data.next_state)
            if data.next_user != '0':
                get_fifth = get_fifth.filter(
                    next_tag_user__id=data.next_user)
 def get_completion_status(self):
        status = {0: 'Open', 1: 'Closed', 2: 'In-Progress'}
        end_key = get_flat_count = 0
        getwfc_status = WorkFlowComment.objects.filter(batch__current_status__survey__id=self.current_status.survey.id,
                                                       batch__current_status__workflow__id=self.current_status.workflow.id).count()
        get_flow_stat = WorkFlowSurveyRelation.objects.filter(
            survey__id=self.current_status.survey.id, workflow__id=self.current_status.workflow.id).order_by('-id')
        if get_flow_stat:
            get_flat_count = get_flow_stat[
                0].workflow.flow_state.filter(active=2).count()
        if getwfc_status == get_flat_count:
            end_key = status.get(1)
        else:
            end_key = status.get(0)
        return end_key
