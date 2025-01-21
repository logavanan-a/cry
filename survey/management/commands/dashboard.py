from django.core.management.base import BaseCommand
from django.core.mail import (EmailMessage,)
from ccd.settings import(EMAIL_HOST_USER,)
from survey.dashboard import (DashBoardData, RegionalHead, NationalHead)


class Command(BaseCommand):

    help = 'Runs crone for DashBoard Data.'

    @staticmethod
    def handle(*args, **options):
        try:
            partner_data = DashBoardData()
            partner_data.data_dump()
            regional = RegionalHead()
            regional.get_dump_data()
            national = NationalHead()
            national.get_dump_data()
        except Exception as e:
            from_ = EMAIL_HOST_USER
            subject = 'Error Log'
            body = e.message
            user_mail_list = ['girish.n.s@mahiti.org']
            email = EmailMessage(subject, body, from_,
                                 user_mail_list,
                                 )
            email.send()
