import os
import smtplib
import time
import uuid
from datetime import datetime

import jwt
from _decimal import Decimal
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from rest_framework import permissions, status
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from academic_year.models import AcademicYear
from account_types.models import AccountType
from appcollections.models import Collection
from bank_accounts.models import BankAccount
from configurations.models import Configuration
from currencies.models import Currency
from finance.settings import SIMPLE_JWT
from financial_years.models import FinancialYear
from mpesa_configs.models import Mpesaconfig
from payment_in_kinds.models import PaymentInKind
from payment_methods.models import PaymentMethod
from reportss.models import OpeningClosingBalances
from school.models import School
from term.models import Term
from voteheads.models import VoteHead, VoteheadConfiguration
from voucher_items.models import VoucherItem


class BaseUserModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_deleted = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True




class SchoolIdMixin:
    def check_school_id(self, request):
        auth_header = get_authorization_header(request).decode('utf-8')
        if not auth_header or 'Bearer ' not in auth_header:
            raise ValidationError({'detail': 'No valid Authorization header'})

        token = auth_header.split(' ')[1]

        try:
            # Decode the JWT token
            decoded_token = jwt.decode(token, SIMPLE_JWT['SIGNING_KEY'], algorithms=[SIMPLE_JWT['ALGORITHM']])
            school_id = decoded_token.get('school_id')

            # Check if the school_id is valid (you may replace this with your validation logic)
            if not is_valid_school_id(school_id):
                raise ValidationError({'detail': 'Invalid school_id'})

            # Do something with the school_id
            return school_id
        except jwt.ExpiredSignatureError:
            raise ValidationError({'detail': 'Token has expired'})
        except jwt.InvalidTokenError:
            raise ValidationError({'detail': 'Invalid token'})


def is_valid_school_id(school_id):
    # Check if any of the UUIDs in the list is valid
    try:
        print(f"Checking schoolId {school_id}")
        School.objects.get(id=school_id)
        uuid.UUID(school_id, version=4)
    except:
        return False
    return True


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.roles.filter(name='ADMIN').exists()


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.roles.filter(name='SUPERUSER').exists()


class IsAdminOrSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_admin or IsAdminUser().has_permission(request,
                                                                                       view) or IsSuperUser().has_permission(
            request, view))


def fetchAllRoles():
    userroles = []
    query_set = Group.objects.all()
    if query_set.count() >= 1:
        for groups in query_set:
            userroles.append(groups)
        return userroles
    else:
        return userroles


def fetchusergroups(userid):
    userroles = []
    query_set = Group.objects.filter(user=userid)
    if query_set.count() >= 1:
        for groups in query_set:
            userroles.append(groups.name)
        return userroles
    else:
        return userroles


def sendMail(sender_email, sender_password, receiver_email, subject, usermessage):
    try:
        message = 'Subject: {}\n\n{}'.format(subject, usermessage)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message)
        print('Email has been sent')
    except Exception as ex:
        raise ValidationError({'detail': str(ex)})


def generate_unique_code(prefix="INV"):
    timestamp = int(time.time())
    random_component = uuid.uuid4().hex[:6]
    unique_code = f"{prefix}{timestamp}{random_component}"
    return unique_code


def UUID_from_PrimaryKey(primarykey):
    id = uuid.UUID(primarykey)
    return id


def file_upload(instance, filename):
    ext = filename.split(".")[-1]
    now = datetime.now()

    if len(str(abs(now.month))) > 1:
        month = str(now.month)
    else:
        month = str(now.month).zfill(2)

    if len(str(abs(now.day))) > 1:
        day = str(now.day)
    else:
        day = str(now.day).zfill(2)

    if len(str(abs(now.hour))) > 1:
        hour = str(now.hour)
    else:
        hour = str(now.hour).zfill(2)

    # upload_to = f"{str(now.year)}/{month}/{day}/{hour}"
    upload_to = f"files"
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid.uuid4().hex, ext)
    return os.path.join(upload_to, filename)





def currentAcademicYear(school_id):
    try:
        return AcademicYear.objects.get(is_current=True, school_id=school_id)
    except AcademicYear.DoesNotExist:
        return None

def currentFinancialYear(school_id):
    try:
        return FinancialYear.objects.get(is_current=True, school=school_id)
    except FinancialYear.DoesNotExist:
        return None

def currentTerm(school_id):
    try:
        return Term.objects.get(is_current=True , school_id=school_id)
    except Term.DoesNotExist:
        return None

def defaultCurrency(school_id):
    try:
        return Currency.objects.get(is_default=True, school=school_id)
    except Currency.DoesNotExist:
        return None

def defaultOverpaymentVoteHead(school_id):
    try:
        return VoteHead.objects.get(is_Overpayment_Default=True, school_id=school_id)
    except VoteHead.DoesNotExist:
        return None

def defaultArrearVoteHead(school_id):
    try:
        return VoteHead.objects.get(is_Arrears_Default=True, school_id=school_id)
    except VoteHead.DoesNotExist:
        return None

def defaultAccountType(school_id):
    try:
        return AccountType.objects.get(is_default=True, school = school_id)
    except AccountType.DoesNotExist:
        return None

def defaultBankAccount(school_id):
    try:
        return BankAccount.objects.get(is_default=True, school = school_id)
    except BankAccount.DoesNotExist:
        return None

def default_MpesaPaymentMethod(school_id):
    try:
        return PaymentMethod.objects.get(is_mpesa_default=True, school = school_id)
    except PaymentMethod.DoesNotExist:
        return None

def defaultMpesaConfiguration(school_id):
    try:
        return Mpesaconfig.objects.get(school_id = school_id)
    except Mpesaconfig.DoesNotExist:
        return None

def defaultconfiguration(school_id):
    try:
        return Configuration.objects.get(school = school_id)
    except Configuration.DoesNotExist:
        return None

def defaultVoteHeadConfiguration(school_id):
    try:
        return VoteheadConfiguration.objects.get(school_id = school_id)
    except VoteheadConfiguration.DoesNotExist:
        return None



def check_if_object_exists(Model, obj_id):
    try:
        instance = Model.objects.get(id=obj_id)
        return True
    except ObjectDoesNotExist:
        return Response({'detail': f"{obj_id} is not a valid uuid"}, status=status.HTTP_400_BAD_REQUEST)







def close_financial_year(current_financial_year,new_financial_year, school_id):

    collectionQuerySet = Collection.objects.filter(
        school_id=school_id,
        receipt__financial_year=current_financial_year,
        receipt__is_reversed=False
    )

    pikQuerySet = PaymentInKind.objects.filter(
        receipt__is_posted=True,
        school_id=school_id,
        receipt__financial_year=current_financial_year,
    )

    expensesQuerySet = VoucherItem.objects.filter(
        voucher__is_deleted=False,
        school_id=school_id,
        voucher__financial_year=current_financial_year,
    )

    closing_cash_at_hand = Decimal(0.0)
    closing_cash_at_bank = Decimal(0.0)

    for collection in collectionQuerySet:
        if collection.receipt.payment_method.is_cash == True:
            closing_cash_at_hand += Decimal(collection.amount)
        elif collection.receipt.payment_method.is_bank == True:
            closing_cash_at_bank += Decimal(collection.amount)
        elif collection.receipt.payment_method.is_cheque == True:
            closing_cash_at_bank += Decimal(collection.amount)

    for pik in pikQuerySet:
        closing_cash_at_hand += Decimal(pik.amoount)

    for voucheritem in expensesQuerySet:
        if voucheritem.receipt.payment_Method.is_cash == True:
            closing_cash_at_hand -= Decimal(voucheritem.amount)
        elif voucheritem.receipt.payment_Method.is_bank == True:
            closing_cash_at_bank -= Decimal(voucheritem.amount)
        elif voucheritem.receipt.payment_method.is_cheque == True:
            closing_cash_at_bank -= Decimal(voucheritem.amount)

    try:
        with transaction.atomic():
            openingClosingBalances_Instance = OpeningClosingBalances.objects.get(financial_year=current_financial_year, school_id=school_id)
            openingClosingBalances_Instance.closing_cash_at_hand = closing_cash_at_hand
            openingClosingBalances_Instance.closing_cash_at_bank = closing_cash_at_bank
            openingClosingBalances_Instance.closing_balance = Decimal(closing_cash_at_hand) + Decimal(closing_cash_at_bank)
            openingClosingBalances_Instance.save()

            new_year = OpeningClosingBalances.objects.create(
                financial_year = new_financial_year,
                opening_cash_at_hand=closing_cash_at_hand,
                opening_cash_at_bank=closing_cash_at_bank,
                opening_balance=Decimal(closing_cash_at_hand) + Decimal(closing_cash_at_bank),
                closing_cash_at_hand=Decimal(0.0),
                closing_cash_at_bank=Decimal(0.0),
                closing_balance=Decimal(0.0),
                school_id=school_id
            )
            new_year.save()

    except Exception as exception:
        return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)







class DefaultMixin:
    def check_defaults(self, request, school_id):

        getdefaultconfiguration = defaultconfiguration(school_id)
        getdefaultVoteHeadConfiguration = defaultVoteHeadConfiguration(school_id)
        # getdefaultMpesaConfiguration = defaultMpesaConfiguration(school_id)
        getcurrentTerm = currentTerm(school_id)
        getcurrentAcademicYear = currentAcademicYear(school_id)
        getcurrentFinancialYear = currentFinancialYear(school_id)
        getdefaultCurrency = defaultCurrency(school_id)
        getdefaultOverpaymentVoteHead = defaultOverpaymentVoteHead(school_id)
        getdefaultArrearVoteHead = defaultArrearVoteHead(school_id)
        getdefaultAccountType = defaultAccountType(school_id)
        getdefaultBankAccount = defaultBankAccount(school_id)
        getdefaultIntegrationPaymentMethod = default_MpesaPaymentMethod(school_id)

        if not getdefaultconfiguration:
            raise ValidationError({'detail': 'Configuration of Receipts and Voucher Numbering not set!'})
        if not getdefaultVoteHeadConfiguration:
            raise ValidationError({'detail': 'VoteHead Configuration Not Set For This Schoool!'})
        # if not getdefaultMpesaConfiguration:
        #     raise ValidationError({'detail': 'Configuration of Mpesa not set for this school!'})
        if not getcurrentTerm:
            raise ValidationError({'detail': 'Current Term not set for this school!'})
        if not getcurrentAcademicYear:
            raise ValidationError({'detail': 'Current Academic Year not set for this school!'})
        if not getcurrentFinancialYear:
            raise ValidationError({'detail': 'Current Financial Year not set for this school!'})
        if not getdefaultCurrency:
            raise ValidationError({'detail': 'Default Currency not set for this school!'})
        if not getdefaultOverpaymentVoteHead:
            raise ValidationError({'detail': 'Default Overpayment VoteHead not set for this school!'})
        if not getdefaultArrearVoteHead:
            raise ValidationError({'detail': 'Default Arrears VoteHead not set for this school!'})
        if not getdefaultAccountType:
            raise ValidationError({'detail': 'Default Account Type not set for this school!'})
        if not getdefaultBankAccount:
            raise ValidationError({'detail': 'Default Bank Account not set for this school!'})
        # if not getdefaultIntegrationPaymentMethod:
        #     raise ValidationError({'detail': 'Default Integration Payment Method not set for this school!'})

