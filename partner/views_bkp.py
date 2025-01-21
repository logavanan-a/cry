class ProjectManagerCreate(CreateAPIView):
    queryset = ProjectuserDetail.objects.filter(active=2)
    serializer_class = ProjectHolderCreateSerializer

    def post(self, request):
        data = Box(request.data)
        serializer_manager = ProjectHolderCreateSerializer(data=data.to_dict())
        serializer_address = AddressSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        try:
            if serializer_manager.is_valid() and serializer_address.is_valid():
                proj_man = ProjectuserDetail.objects.create(
                    user_type=2, project_id=data.proj_id, name=data.name, contact_address=int(data.contact_address))
                contact = literal_eval(data.get_contact)
                addr = Address.objects.create(office=5, address1=data.address1, address2=data.address2,
                                              boundary_id=data.boundary, pincode=data.pincode)
                addr.content_type, addr.object_id = ContentType.objects.get_for_model(
                    proj_man), proj_man.id
                addr.save()
                for con in contact:
                    con_data = Box(con)
                    con = ContactDetail.objects.create(priority=int(con_data.priority) if int(con_data.priority) <= 3 else 3,
                                                       contact_no=con_data.mobile, email=con_data.email, landline=con_data.landline, fax=con_data.fax,
                                                       content_type=ContentType.objects.get_for_model(addr), object_id=addr.id)
                response = {'status': 2, 'message': 'successfully created',
                            'project_manager': proj_man.id, 'project_id': int(data.proj_id)}
            else:
                response.update(errors1=serializer_manager.errors,
                                errors2=serializer_address.errors)
        except:
            pass
        return Response(response)


class PartnerDetailView(CreateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerDetailViewSerializer

    @staticmethod
    def get_project_details(self, part):
        try:
            proj = Project.objects.get(active=2, partner=part)
            proj_name = proj.title
            proj_legal_registration = 1 if proj.other_legal_registration else 0
            proj_legal_name = proj.legal_name if proj.legal_name else ''
            proj_legal_number = proj.legal_number if proj.legal_name else ''
            proj_disbursal = proj.disbursal.id if proj.disbursal else ''
            proj_pre_funding = proj.pre_funding.id if proj.pre_funding else ''
            proj_fla_grm_team = proj.fla_grm_team.id if proj.fla_grm_team else ''
            proj_boundary = [
                int(b.id) for b in proj.boundary.all()] if proj.boundary.all() else ''
            proj_community = [
                int(c.id) for c in proj.community.all()] if proj.community.all() else ''
            proj_theme = [int(t.id) for t in proj.theme.all()
                          ] if proj.theme.all() else ''
            proj_prominent_issues = [int(po.id) for po in proj.prominent_issues.all(
            )] if proj.prominent_issues.all() else ''
            proj_remarks = proj.remarks if proj.remarks else ''
            try:
                doc = DocumentCategory.objects.get(
                    slug='pre-funding-visit-done')
                attach = Attachments.objects.get(
                    document_category=doc, object_id=proj.id)
                proj_attach = attach.attachment.url if attach.attachment else ''
            except:
                proj_attach = ''
            try:
                team_doc = DocumentCategory.objects.get(
                    slug='fla-cleared-from-grm-team')
                team_attach = Attachments.objects.get(
                    document_category=team_doc, object_id=proj.id)
                proj_team = team_attach.attachment.url if team_attach.attachment else ''
            except:
                proj_team = ''
            get_part_project = {'proj_boundary': proj_boundary,
                                'proj_community': proj_community,
                                'proj_disbursal': proj_disbursal,
                                'proj_fla_grm_team': proj_fla_grm_team,
                                'proj_fla_grm_team_file': proj_team,
                                'proj_legal_name': proj_legal_name,
                                'proj_legal_number': proj_legal_number,
                                'proj_legal_registration': proj_legal_registration,
                                'proj_name': proj_name,
                                'proj_pre_funding': proj_pre_funding,
                                'proj_pre_funding_file': proj_attach,
                                'proj_prominent_issues': proj_prominent_issues,
                                'proj_remarks': proj_remarks,
                                'proj_theme': proj_theme,
                                'proj_id': proj.id}
        except:
            get_part_project = {'status': 0, 'message': 'something went wrong'}
        return get_part_project

    @staticmethod
    def get_project_holder(self, proj):
        try:
            get_holder_contact = []
            proj_holder = ProjectuserDetail.objects.get(
                active=2, user_type=1, project=proj)
            proj_holder_name = proj_holder.name
            proj_contact_holder = ContactDetail.objects.filter(
                active=2, object_id=proj_holder.id).order_by('priority')
            if proj_contact_holder:
                get_holder_contact = [{'id': ph.id, 'priority': ph.priority, 'contact_no': ph.contact_no,
                                       'email': ph.email, 'landline': ph.landline, 'fax': ph.fax}
                                      for ph in proj_contact_holder]
            project_holder = {
                'id': proj_holder.id, 'project_holder': proj_holder_name, 'contacts': get_holder_contact}
        except:
            project_holder = {'status': 0, 'message': 'something went wrong'}
        return project_holder

    @staticmethod
    def get_project_manager(self, proj):
        try:
            get_project, get_manager_contact = {}, []
            proj_manager = ProjectuserDetail.objects.get(
                active=2, user_type=2, project=proj)
            proj_manager_name = proj_manager.name
            proj_contact_address = 1 if proj_manager.contact_address else 0
            proj_manager_addr = Address.objects.get(
                active=2, office=5, object_id=proj_manager.id)
            proj_manager_address1 = proj_manager_addr.address1
            proj_manager_address2 = proj_manager_addr.address2
            proj_manager_boundary = proj_manager_addr.boundary.id if proj_manager_addr.boundary else ''
            proj_manager_pincode = proj_manager_addr.pincode
            proj_manager_contact = ContactDetail.objects.filter(
                active=2, object_id=proj_manager_addr.id).order_by('priority')
            if proj_manager_contact:
                get_manager_contact = [{'id': ph.id, 'priority': ph.priority, 'contact_no': ph.contact_no,
                                        'email': ph.email, 'landline': ph.landline, 'fax': ph.fax}
                                       for ph in proj_manager_contact]
            get_project.update(name=proj_manager_name, id=proj_manager.id, address1=proj_manager_address1, address2=proj_manager_address2,
                               boundary=proj_manager_boundary, pincode=proj_manager_pincode, contacts=get_manager_contact, proj_manager_address=proj_manager_addr.id,
                               contact_address=proj_contact_address)
        except:
            get_project = {'status': 0, 'message': 'something went wrong'}
        return get_project

    @staticmethod
    def get_partner_address(self, part):
        get_address = Address.objects.filter(active=2, object_id=part.id)
        try:
            get_address_dict = {}
            for gd in get_address:
                get_address_dict.setdefault(gd.get_office_display(), {})
                get_add = {'address1': gd.address1, 'address2': gd.address2,
                           'boundary': gd.boundary.id if gd.boundary else '',
                           'pincode': gd.pincode, 'id': gd.id, 'office_type': gd.office}
                get_add_con = ContactDetail.objects.filter(
                    active=2, object_id=gd.id).order_by('priority')
                get_addr_contact = [{'id': g.id, 'priority': g.priority, 'contact_no': g.contact_no,
                                     'email': g.email, 'landline': g.landline, 'fax': g.fax}
                                    for g in get_add_con]
                get_add.update(contacts=get_addr_contact)
                get_address_dict.get(gd.get_office_display()).update(get_add)
        except:
            get_address_dict = {'status': 0, 'message': 'something went wrong'}
        return get_address_dict

    @staticmethod
    def get_partner_reg(self, part):
        get_part_reg = {'status': 0, 'message': 'something went wrong'}
        try:
            get_reg = Registration.objects.filter(
                active=2, object_id=part.id).order_by('priority')
            get_part_reg = [{'act': gr.act,
                             'attachment': gr.attachment.url if gr.attachment else '',
                             'date_of_registered': gr.date_of_registered.strftime('%Y-%m-%d') if gr.date_of_registered else '',
                             'due_date': gr.due_date.strftime('%Y-%m-%d') if gr.due_date else '',
                             'name': gr.name,
                             'pan': gr.pan,
                             'priority': gr.priority,
                             'status': gr.status,
                             'tan': gr.tan,
                             'tin': gr.tin, 'id': gr.id} for gr in get_reg]
        except:
            pass
        return get_part_reg

    @staticmethod
    def get_partner_bank(self, part):
        get_part_reg = {'status': 0, 'message': 'something went wrong'}
        try:
            get_bank = BankAccount.objects.filter(
                active=2, object_id=part.id).order_by('priority')
            get_part_reg = [{'account_number': bn.account_number,
                             'account_type': bn.account_type,
                             'bank_name': bn.bank_name,
                             'branch_name': bn.branch_name,
                             'ifsc_code': bn.ifsc_code,
                             'priority': bn.priority, 'id': bn.id} for bn in get_bank]
        except:
            pass
        return get_part_reg

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerDetailViewSerializer(data=data.to_dict())
        project_holder = project_manager = ''
        partner_details = {'status': 0, 'message': 'something went wrong'}
        try:
            if serializer.is_valid():
                part = Partner.objects.get(active=2, id=data.p_id)
                proj = Project.objects.filter(active=2, partner=part)
                part_name = part.name
                part_partner_id = part.partner_id
                part_region_id = part.region.id if part.region else ''
                part_state = part.state.id if part.state else ''
                part_nature_of_partner = part.nature_of_partner.id if part.nature_of_partner else ''
                part_status = part.status.id if part.status else ''
                part_support_since = part.support_since.strftime(
                    '%Y-%m-%d') if part.support_since else ''
                part_admin_id = {'username': part.user.username, 'email': part.user.email, 'id': part.user.id,
                                 'admin_id': part.admin_id if part.admin_id else ''} if part.user else ''
                partner_details = {}
                partner_details.update(partner_id=part.id, name=part_name, unique_id=part_partner_id, region=part_region_id,
                                       state=part_state, nature_of_partner=part_nature_of_partner,
                                       status=part_status, support_since=part_support_since, admin_id=part_admin_id)
                project_details = self.get_project_details(self, part)
                if proj:
                    project_holder = self.get_project_holder(self, proj[0])
                    project_manager = self.get_project_manager(self, proj[0])
                partner_address = self.get_partner_address(self, part)
                partner_reg = self.get_partner_reg(self, part)
                partner_bank = self.get_partner_bank(self, part)
                partner_details.update(project=project_details, holder=project_holder, manager=project_manager,
                                       address=partner_address, registration=partner_reg, bank=partner_bank)
            else:
                partner_details.update(errors=serializer.errors)
        except:
            pass
        return Response(partner_details)


class PartnerEdit(CreateAPIView):
    queryset = Partner.objects.filter(active=2)
    serializer_class = PartnerEditSerializer

    def post(self, request):
        data = Box(request.data)
        serializer = PartnerEditSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'something went wrong'}
        if serializer.is_valid():
            partner = Partner.objects.filter(active=2, id=data.part_id)
            if partner:
                part = partner[0]
                part.name = data.name
                part.region_id = data.region
                part.state_id = data.state
                part.nature_of_partner_id = data.nature_of_partner
                part.status_id = data.status
                part.support_since = data.support_since
                admin = Box(literal_eval(data.user))
                part.user.username = admin.username
                part.user.email = admin.email
                part.user.save()
                part.save()
                proj = Project.objects.filter(active=2, partner=part)
                if proj:
                    pro = proj[0]
                    pro.title = data.project_name
                    pro.other_legal_registration = 1 if data.other_legal_registration == 'true' else 0
                    pro.legal_name = data.legal_name
                    pro.legal_number = data.legal_number
                    pro.disbursal_id = data.disbursal
                    pro.pre_funding_id = data.pre_funding
                    pro.fla_grm_team_id = data.fla_grm_team
                    pro.boundary.clear()
                    pro.boundary.add(*data.boundary.split(','))
                    pro.community.clear()
                    pro.community.add(*data.community.split(','))
                    pro.theme.clear()
                    pro.theme.add(*data.theme.split(','))
                    pro.prominent_issues.clear()
                    pro.prominent_issues.add(*data.prominent_issues.split(','))
                    pro.remarks = data.remarks
                    pro.save()
                    try:
                        if data.pre_funding_file:
                            doc, created = DocumentCategory.objects.get_or_create(name='Pre Funding Visit Done',
                                                                                  slug='pre-funding-visit-done')
                            attach, created = Attachments.objects.get_or_create(
                                document_category=doc, content_type=ContentType.objects.get_for_model(pro), object_id=pro.id)
                            attach.attachment = data.pre_funding_file
                            attach.save()
                    except:
                        pass
                    try:
                        if data.team_file:
                            team_doc, created = DocumentCategory.objects.get_or_create(name='FLA cleared from GRM Team',
                                                                                       slug='fla-cleared-from-grm-team')
                            attach, created = Attachments.objects.get_or_create(
                                document_category=team_doc, content_type=ContentType.objects.get_for_model(pro), object_id=pro.id)
                            attach.attachment = data.team_file
                            attach.save()
                    except:
                        pass
                    # Project Holder Update
                    proj_holder = ProjectuserDetail.objects.filter(
                        active=2, user_type=1, project=pro)
                    if proj_holder:
                        proj_hold = proj_holder[0]
                        proj_holder_ = literal_eval(data.project_holder)[0]
                        pro_ = Box(proj_holder_)
                        proj_hold.name = pro_.name
                        proj_hold.save()
                        proj_contact_holder = ContactDetail.objects.filter(
                            active=2, object_id=proj_hold.id).order_by('priority').delete()
                        for con in pro_.contact:
                            con_data = Box(con)
                            con = ContactDetail.objects.create(priority=int(con_data.priority) if int(con_data.priority) <= 3 else 3, contact_no=con_data.mobile,
                                                               email=con_data.email, landline=con_data.landline,
                                                               fax=con_data.fax, content_type=ContentType.objects.get_for_model(proj_hold), object_id=proj_hold.id)
                    # Project Manager Update
                    proj_man = ProjectuserDetail.objects.filter(
                        active=2, user_type=2, project=pro)
                    if proj_man:
                        project_man = proj_man[0]
                        proj_man_ = literal_eval(data.project_manager)[0]
                        manager = Box(proj_man_)
                        project_man.name = manager.name
                        project_man.contact_address = int(
                            manager.contact_address)
                        project_man.save()
                        contact = manager.contact
                        addr, created = Address.objects.get_or_create(
                            office=5, content_type=ContentType.objects.get_for_model(project_man), object_id=project_man.id)
                        addr.address1 = manager.address1
                        addr.address2 = manager.address2
                        addr.boundary_id = manager.boundary
                        addr.pincode = manager.pincode
                        addr.save()
                        proj_contact_manager = ContactDetail.objects.filter(
                            active=2, object_id=addr.id).order_by('priority').delete()
                        for con in contact:
                            con_data = Box(con)
                            con = ContactDetail.objects.create(priority=int(con_data.priority) if int(con_data.priority) <= 3 else 3,
                                                               contact_no=con_data.mobile, email=con_data.email, landline=con_data.landline, fax=con_data.fax,
                                                               content_type=ContentType.objects.get_for_model(addr), object_id=addr.id)
                # Bank Details
                get_banks = BankAccount.objects.filter(
                    active=2, object_id=part.id).order_by('priority')
                if get_banks:
                    get_banks.delete()
                    get_bank = literal_eval(data.bank)
                    for b in get_bank:
                        bank_ = Box(b)
                        create_bank = BankAccount.objects.create(priority=int(bank_.priority),
                                                                 account_number=bank_.account_number,
                                                                 account_type=int(
                                                                     bank_.account_type),
                                                                 bank_name=bank_.bank_name,
                                                                 branch_name=bank_.branch_name,
                                                                 ifsc_code=bank_.ifsc_code)
                        create_bank.content_type, create_bank.object_id = ContentType.objects.get_for_model(
                            part), part.id
                        create_bank.save()
                # Registration Details
                get_reg = Registration.objects.filter(
                    active=2, object_id=part.id).order_by('priority')
                if get_reg:
                    get_reg.delete()
                    get_register = literal_eval(data.registration)
                    for rg in get_register:
                        reg_ = Box(rg)
                        create_reg = Registration.objects.create(
                            name=reg_.name,
                            act=reg_.act,
                            date_of_registered=reg_.date_of_registered,
                            status=reg_.status,
                            priority=int(reg_.priority),
                            pan=reg_.pan,
                            tan=reg_.tan,
                            tin=reg_.tin,
                            due_date=reg_.due_date,)
                        create_reg.content_type, create_reg.object_id = ContentType.objects.get_for_model(
                            part), part.id
                        create_reg.save()
                if data.attachment:
                    create_reg.attachment = data.attachment
                    create_reg.save()
                get_address = Address.objects.filter(
                    active=2, office__in=[1, 2, 3, 4], object_id=part.id)
                if get_address:
                    for con in get_address.values_list('id', flat=True):
                        cd = ContactDetail.objects.filter(
                            active=2, object_id=con)
                        if cd:
                            cd.delete()
                    get_address.delete()
                get_all_address = literal_eval(data.address)
                if get_all_address:
                    for gd in get_all_address:
                        g = Box(gd)
                        gad = Address.objects.create(
                            office=g.office,
                            address1=g.address1,
                            address2=g.address2,
                            boundary_id=g.boundary,
                            pincode=g.pincode)
                        gad.content_type, gad.object_id = ContentType.objects.get_for_model(
                            part), part.id
                        gad.save()
                        get_con = g.contact
                        for get_add_con in get_con:
                            con_data_ad = Box(get_add_con)
                            con = ContactDetail.objects.create(priority=int(con_data_ad.priority) if int(con_data_ad.priority) <= 3 else 3,
                                                               contact_no=con_data_ad.mobile, email=con_data_ad.email, landline=con_data_ad.landline, fax=con_data_ad.fax,
                                                               content_type=ContentType.objects.get_for_model(gad), object_id=gad.id)
                response = {'status': 2,
                            'message': 'successfully updated the partner'}
        else:
            response.update(errors=serializer.errors)
        return Response(response)

# class AdministrationCreate(CreateAPIView):
#     queryset = User.objects.filter(is_active=True)
#     serializer_class = AdminSerializer

#     def post(self, request):
#         data = Box(request.data)
#         serializer = AdminSerializer(data=data.to_dict())
#         response = {'status':0,'message':'Something went wrong'}
#         try:
#             if serializer.is_valid():
#                 user = User.objects.create_user(data.username, data.email, data.password)
#                 if user:
#                     partner = Partner.objects.get(active=2, id=int(data.p_id))
#                     partner.user = user
#                     partner.admin_id = 'ADMIN-' + str(user.id)
#                     partner.save()
#                     response = {'status':2,'message':'Successfully created','partner_id':partner.id}
#             else:
#                  errors_ = {}
#                  errors = [errors_.update({k:serializer.errors.get(k)[0]}) for k in serializer.errors.keys()]
#                  if errors_.keys()[0] == 'non_field_errors':
#                      if errors_.get('non_field_errors') == 'Name contains numbers or special characters.':
#                         errors_['username'] =  errors_.pop('non_field_errors')
#                      else:
#                         errors_['password'] =  errors_.pop('non_field_errors')
#                  response.update(errors=errors_)
#         except IntegrityError:
#              response.update(errors={'username':'Username already exists'})
#         return Response(response)


class AddressEdit(UpdateAPIView):
    queryset = Address.objects.filter(active=2)
    serializer_class = AddressSerializer

    def update(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = AddressSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            check_add = self.queryset.filter(
                id=int(self.kwargs['pk']), office=int(data.office))
            if check_add:
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=data.to_dict(), partial=False)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                response = {
                    'status': 2, 'message': 'Successfully updated for the address id: %(pk)s' % self.kwargs}
            else:
                response.update(
                    errors={'office': 'Already for given office type may exists or not please check.'})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class RegistrationEdit(UpdateAPIView):
    queryset = Registration.objects.filter(active=2)
    serializer_class = RegistrationSerializer

    def update(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = RegistrationSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            check_add = self.queryset.filter(
                id=int(self.kwargs['pk']), reg_type=int(data.reg_type))
            if check_add:
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=data.to_dict(), partial=False)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                if data.exp_date:
                    instance.exp_date = instance.exp_date
                if data.attachment:
                    instance.attachment = instance.attachment
                instance.save()
                response = {
                    'status': 2, 'message': 'Successfully updated for the registration id: %(pk)s' % self.kwargs}
            else:
                response.update(errors={
                                'registration': 'Already for given registration type may exists or not please check.'})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class BankAccountEdit(UpdateAPIView):
    queryset = BankAccount.objects.filter(active=2)
    serializer_class = BankAccountEditSerializer

    def update(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = BankAccountEditSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went  wrong.'}
        if serializer.is_valid():
            instance = self.get_object()
            check_add = self.queryset.filter(
                id=int(self.kwargs['pk']), priority=int(data.priority))
            if check_add:
                get_acc = self.queryset.filter(
                    id=int(self.kwargs['pk']), account_number=instance.account_number)
                if not get_acc:
                    serializer = self.get_serializer(
                        instance, data=data.to_dict(), partial=False)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                    response = {
                        'status': 2, 'message': 'Successfully updated for the bank detail-id: %(pk)s' % self.kwargs}
            else:
                response.update(
                    errors={'bank': 'Already for given bank priority may exists or not please check.'})
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)

== == == == == == == == == == == == == == == == == = funding edit == == == == == == == == == == == == == == == == == == == == == =

    def get_store_year(self, tof, start_, end_):
        if tof == '0':
            budget_year, created = BudgetYear.objects.get_or_create(
                start_year=start_, end_year=end_)
        elif tof == '1':
            budget_year, created = BudgetYear.objects.get_or_create(
                start_year=start_, end_year=date(start_[1], 1, 1))
        elif tof == '2':
            budget_year, created = BudgetYear.objects.get_or_create(
                start_year=start_, end_year=end_)
        return budget_year

    def get_project_support_to(self, proj_id):
        start_year = end_year = ''
        proj = Project.objects.filter(active=2, id=int(proj_id))
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
        return start_year, end_year

    def alter_instance(self):
        status_funds = check_fund_exists(self.get_queryset(), data.to_dict())
        instance_tof = {'0': lambda: (instance.year.start_year, instance.year.end_year),
                        '1': lambda: ('{0} - {1}'.format(instance.year.start_year.year, instance.year.end_year.year), 0),
                        '2': lambda: (instance.year.start_year, instance.year.end_year)}
        tof = {'0': lambda: (entire_start_years.strftime('%Y-%m-%d'), entire_end_years.strftime('%Y-%m-%d')),
               '1': lambda: (start_year_, end_year_),
               '2': lambda: (datetime.strptime(start_year_, '%Y-%m-%d'), datetime.strptime(end_year_, '%Y-%m-%d'))}


class FundingThematicListing(CreateAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = DatetoYearSerializer

    def post(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = DatetoYearSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        if serializer.is_valid():
            get_remain_theme = self.get_queryset().filter(theme_budget__id=int(
                data.thematic_id), object_id=int(data.proj_id)).values_list('id', flat=True)
            fun = Funding.objects.filter(active=2, object_id=int(data.proj_id))
            if fun:
                get_fun_theme = ConfigureThematic.objects.filter(
                    funding=fun[0], funding_theme__id=int(data.thematic_id))
                if get_fun_theme:
                    get_budget_config = get_fun_theme[0].thematic.filter(
                        active=2).values_list('id', flat=True)
                    get_remain_theme = set(
                        get_remain_theme) ^ set(get_budget_config)
            get_thematic = map(lambda x: BudgetConfig.objects.get(
                id=int(x)), get_remain_theme)
            response = {'status': 2, 'message': 'Successfully Retrieved the Item Liner',
                        'data': [{'id': g.id, 'item': g.line_item} for g in get_thematic]}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)


class FundingThematicListing(CreateAPIView):
    queryset = BudgetConfig.objects.filter(active=2)
    serializer_class = DatetoYearSerializer

    def get_comb_next_years(self, list_, d):
        mast_ = 0
        for i, q in enumerate(list_):
            sy = map(int, q.split('-'))
            sy.sort()
            if sy[0] == d:
                mast_ = i
        final_years = map(int, list_[mast_].split(' - '))
        final_years.sort()
        return final_years

    def get_project_support_to(self, proj_id):
        start_year = end_year = ''
        proj = Project.objects.filter(active=2, id=int(proj_id))
        if proj:
            p = proj[0]
            start_year = p.program.partner.support_from
            end_year = p.program.partner.support_to
        return start_year, end_year

    def entire_project(self, **kwargs):
        data = Box(kwargs)
        theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id),
                                           object_id=int(data.proj_id)).values_list('id', flat=True)
        return theme

    def get_years_(self, *args, **kwargs):
        data = Box(kwargs)
        start_years = map(
            int, map(lambda x: x.strip(), re.split('-', args[0])))
        start_years.sort(key=int)
        theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id), object_id=int(data.proj_id),
                                           year__start_year__year__gte=start_years[0], year__end_year__year__lte=start_years[1]).values_list('id', flat=True)
        return theme

    def get_custom_column_(self, *args, **kwargs):
        data = Box(kwargs)
        args = [a.strftime('%Y-%m-%d').split('-') for a in args if a]
        sort_args = [ar.sort(key=int) for ar in args]
        years = list(set([int(a[2]) for a in args if a]))
        get_start_years, get_end_years = self.get_project_support_to(
            data.proj_id)
        diff_year = get_end_years.year - get_start_years.year
        get_date = Convert_Date_to_Year(diff_year, get_start_years.year)
        get_years = get_date.convert_year()
        if len(years) == 1:
            get_next_years_ = self.get_comb_next_years(get_years, years[0])
            end_year_ = date(get_next_years_[1], 1, 1)
            theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id), object_id=int(data.proj_id),
                                               year__start_year__year__gte=get_next_years_[0], year__end_year=end_year_).values_list('id', flat=True)
        else:
            years.sort()
            theme = self.get_queryset().filter(theme_budget__id=int(data.thematic_id), object_id=int(data.proj_id),
                                               year__start_year__year__gte=years[0], year__end_year__year__lte=years[1]).values_list('id', flat=True)
        return theme

    def post(self, request, *args, **kwargs):
        data = Box(request.data)
        serializer = DatetoYearSerializer(data=data.to_dict())
        response = {'status': 0, 'message': 'Something went wrong'}
        start_year_ = data.start_year
        end_year_ = data.end_year
        entire_start_years, entire_end_years = self.get_project_support_to(
            data.proj_id)
        tof = {'0': lambda: (entire_start_years.strftime('%Y-%m-%d'), entire_end_years.strftime('%Y-%m-%d')),
               '1': lambda: (start_year_, end_year_),
               '2': lambda: (datetime.strptime(start_year_, '%Y-%m-%d'), datetime.strptime(end_year_, '%Y-%m-%d'))}
        start_years, end_years = tof.get(data.type_funding)()
        get_years_thematics = {'0': lambda: self.entire_project(**data.to_dict()),
                               '1': lambda: self.get_years_(start_year_, **data.to_dict()),
                               '2': lambda: self.get_custom_column_(start_years, end_years, **data.to_dict())}
        if serializer.is_valid():
            get_remain_theme = get_years_thematics.get(data.type_funding)()
            fun = Funding.objects.filter(active=2, object_id=int(data.proj_id))
            if fun:
                get_fun_theme = ConfigureThematic.objects.filter(
                    active=2, funding=fun[0], funding_theme__id=int(data.thematic_id))
                if get_fun_theme:
                    get_budget_config = get_fun_theme[0].thematic.filter(
                        active=2).values_list('id', flat=True)
                    get_remain_theme = set(
                        get_remain_theme) ^ set(get_budget_config)
            get_thematic = map(lambda x: BudgetConfig.objects.get(
                id=int(x)), get_remain_theme)
            response = {'status': 2, 'message': 'Successfully Retrieved the Item Liner',
                        'data': [{'id': g.id, 'item': g.line_item} for g in get_thematic]}
        else:
            response.update(errors=unpack_errors(serializer.errors))
        return Response(response)["state", "district", "block", "gramaPanchayath", "village", "hamlet"]["state", "district", "city", "area", "ward", "mohalla-slum"]


class LiveSearch(object):
    __slots__ = ('queryset', 'username')

    def get_results(self):
        users_data = []
        if self.username:
            get_name = self.username.split(',')
            all_names = lambda x: [{'id': u.id, 'name': u.username} for u in User.objects.filter(
                is_active=True, username__startswith=x)]
            full_list = [all_names(name) for name in get_name]
            users_data = chain.from_iterable(full_list)
        return users_data

1st:
user = 1
donar = 6
proj_id = 93
types_of_funding = 2
start_year = 2017 - 05
end_year = 2018 - 01
status = 202
probability_status = 207
thematic_id = ["110", "111", "112"]
line_item_id = ["194", "195", "196", "197", "198", "199"]

2nd:
user = 1
donar = 7
proj_id = 93
types_of_funding = 2
start_year = 2018 - 02
end_year = 2019 - 01
status = 200
probability_status = 206
thematic_id = ["109", "110", "111"]
line_item_id = ["204", "205", "206", "207", "209"]
