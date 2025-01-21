from ast import literal_eval
import csv
from django.contrib.auth.admin import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.core.mail import (EmailMessage,)
from ccd.settings import(BASE_DIR)
from masterdata.models import (Boundary, DynamicContent)
from partner.models import (PartnerReportFile,)

EMAIL_HOST_USER = 'admin@meal.mahiti.org'


class Command(BaseCommand):
    help = 'Runs crone to generate report using csv data.'

    def get_repr(self, value):
        if callable(value):
            return '%s' % value()
        return value

    def get_field(self, instance, field):
        field_path = field.split('.')
        attr = instance
        for elem in field_path:
            try:
                attr = getattr(attr, elem)
            except AttributeError:
                return None
        return attr

    def add_arguments(self, parser):
        parser.add_argument('data', type=str)
        parser.add_argument(
            'location_ids',
            type=str
        )

    def handle(self, *args, **options):
        from_ = EMAIL_HOST_USER
        try:
            data = literal_eval(options['data'])
            location_ids = literal_eval(options['location_ids'])
            location = Boundary.objects.filter(
                id__in=location_ids)
            headers = data.get('display_headers', [])
            level_name = data.get('level_name', [])
            level_headers = data.get('level_headers', [])
            user_id = data.get('user_id', 0)
            location_name = data.get('location_name')
            location_type = data.get('location_type')
            user_email = User.objects.get(id=int(user_id))
            user_name = user_email.first_name + ' ' + user_email.last_name
            with open(BASE_DIR + '/static/' + 'location_report.csv', 'wb+') as f:
                write = csv.writer(f)
                write.writerow(headers)
                for loc in location:
                    location_list = []
                    for level, head in zip(level_name, level_headers):
                        obj = self.get_repr(self.get_field(loc, level))
                        location_list.append(obj)
                    write.writerow(location_list)
                part_report = PartnerReportFile.objects.create(user=user_email,
                                                               name='location_report')
                part_report.report.save(f.name, File(f))
            download = BASE_DIR + '/' + part_report.report.url
            email_file_name = 'Location-Report.csv'
            get_content = DynamicContent.objects.get(active=2, content_type=1)
            sub = get_content.subject.format(location_name)
            body = get_content.content.format(
                location_name, user_name, location_type)
            user_mail_list = [user_email.email]
            email = EmailMessage(sub, body, from_,
                                 user_mail_list,
                                 )
            attachment = open(download, 'rb+')
            email.attach(email_file_name, attachment.read(), 'application/csv')
            email.send()
        except Exception as e:
            sub = e.message
            body = 'Dear Team, \n\n Please find the Task Report attached along with this mail.'
            user_mail_list = ['pradam.abhilash@mahiti.com']
            email = EmailMessage(sub, body, from_,
                                 user_mail_list,
                                 )
            email.send()
