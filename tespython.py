from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from rest_framework.exceptions import NotFound

from appcollections.models import Collection
from appcollections.serializers import CollectionSerializer
from bank_accounts.models import BankAccount
from constants import RATIO, PRIORITY
from invoices.models import Invoice
from mpesa_configs.models import Mpesaconfig
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from reportss.models import trackBalance
from students.models import Student
from transactions.models import Transaction
from utils import currentAcademicYear, currentFinancialYear, currentTerm, defaultAccountType, defaultCurrency, \
    defaultBankAccount, defaultOverpaymentVoteHead, generate_unique_code, default_MpesaPaymentMethod
from voteheads.models import VoteheadConfiguration, VoteHead


def transform_phone_number(phone_number):
    phonenumber = str(phone_number)
    print(f"Trying ", phonenumber)
    if not phonenumber:
        return phonenumber
    if phonenumber == "":
        return phonenumber
    if phonenumber.startswith('0'):
        print("It starts with zero")
        return '254' + phonenumber[1:]
    elif phonenumber.startswith('+254'):
        return phonenumber[1:]
    else:
        return phonenumber





# import base64
#
# file_path = "C:\\Users\\kaita\\OneDrive\\Desktop\\coatOfArms.png"
#
# with open(file_path, "rb") as file:
#     encoded_content = base64.b64encode(file.read()).decode("utf-8")
#
# print(encoded_content)


# dated = "12/10/2023"
# date_of_admission = str(dated)
# print(date_of_admission)


import base64
import requests


















class MpesaInit:
    def __init__(self, school_id):

        if school_id:
            try:
                configuration = Mpesaconfig.objects.get(school_id=school_id)
            except ObjectDoesNotExist:
                raise NotFound("Mpesa configuration not found for the specified school.")

            self.registration_url = configuration.registration_url
            self.token_url = configuration.token_url
            self.short_code = configuration.paybill_number
            self.response_type = "Canceled"
            self.confirmation_url = configuration.callback_url
            self.validation_url = configuration.callback_url
            self.consumer_key = configuration.consumer_key
            self.consumer_secret = configuration.consumer_secret


    def generate_password(self, consumer_key, consumer_secret):
        credentials = f"{consumer_key}:{consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded_credentials}"


    def generate_access_token(self):
        authorization = self.generate_password(self.consumer_key, self.consumer_secret)
        headers = {'Authorization': authorization}
        response = requests.get(self.token_url, headers=headers)

        if response.status_code == 200:
            token = response.json().get('access_token')
            return token
        else:
            return f"Error: {response.status_code} - {response.text}"

    def register_confirmation_and_validation_url(self):
        access_token = self.generate_access_token()
        print(access_token)

        payload = {
            "ShortCode": self.short_code,
            "ResponseType": self.response_type,
            "ConfirmationURL": self.confirmation_url,
            "ValidationURL": self.confirmation_url
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        try:
            response = requests.post(self.registration_url, json=payload, headers=headers)
            print(f"{self.confirmation_url}")
            print(response.status_code)
            print(response.json())
            response_data = response.json()
            response_code = response_data.get('ResponseCode')
            if response_code != '0':
                raise Exception(response_data)

        except Exception as exception:
            raise Exception(exception)

    def callback(self, data):
        print(f"Data is {data}")

        transactionType = data.get('TransactionType', '')
        transID = data.get('TransID', '')
        transTime = data.get('TransTime', '')
        transAmount = data.get('TransAmount', '')
        businessShortCode = data.get('BusinessShortCode', '')
        billRefNumber = data.get('BillRefNumber', '')
        invoiceNumber = data.get('InvoiceNumber', '')
        orgAccountBalance = data.get('OrgAccountBalance', '')
        thirdPartyTransID = data.get('ThirdPartyTransID', '')
        mSISDN = data.get('MSISDN', '')
        firstName = data.get('FirstName', '')
        middleName = data.get('MiddleName', '')
        lastName = data.get('LastName', '')

        transaction_time = datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        mobile_number = mSISDN

        paid_by = f'{firstName} {middleName} {lastName}'
        paybill = businessShortCode
        admission_number = billRefNumber
        amount_paid = transAmount
        transaction_id = transID
        transaction_type = transactionType

        print(f"-0.0.0.0")

        try:
            student = Student.objects.get(admission_number=admission_number)
            print(f"Student is not none")
        except ObjectDoesNotExist:
            print(f"Student is none")
            student = None

        try:
            from django.db import transaction
            with transaction.atomic():

                school = Mpesaconfig.objects.get(paybill_number=paybill)
                school_id = school.school_id

                status = "PENDING"
                if student == None:
                    status = "PENDING"

                transaction = Transaction.objects.create(
                    mobile=mobile_number,
                    purpose="FEES",
                    transid=transaction_id,
                    timestamp=transaction_time,
                    amount=Decimal(amount_paid),
                    student=student,
                    school_id=school_id,
                    status=status,
                    paid_by=paid_by,
                    transaction_type=transaction_type,
                    thirdPartyTransID=thirdPartyTransID,
                    orgAccountBalance = orgAccountBalance,
                    invoiceNumber = invoiceNumber,
                )

                print(f"Transactions created")


                if student != None:
                    print(f"student is not null")
                    to_receipt = True

                    receipt_no = generate_unique_code("RT")
                    academic_year = currentAcademicYear(school_id)
                    term = currentTerm(school_id)
                    financial_year = currentFinancialYear(school_id)
                    accounttype = defaultAccountType(school_id)
                    currency = defaultCurrency(school_id)
                    bankAccount = defaultBankAccount(school_id)
                    thedefault_MpesaPaymentMethod = default_MpesaPaymentMethod(school_id)

                    if not academic_year:
                        to_receipt  = False
                        print(f"Not 1")
                    if not term:
                        to_receipt = False
                        print(f"Not 2")
                    if not financial_year:
                        to_receipt = False
                        print(f"Not 3")
                    if not accounttype:
                        to_receipt = False
                        print(f"Not 4")
                    if not currency:
                        to_receipt = False
                        print(f"Not 5")
                    if not bankAccount:
                        to_receipt = False
                        print(f"Not 6")
                    if not thedefault_MpesaPaymentMethod:
                        print(f"Not 7")
                        to_receipt = False

                    if not to_receipt:
                        print(f"It is not to receippt")
                        transaction.status = "PENDING"
                        transaction.save()
                    else:

                        try:
                            votehead_configuration = VoteheadConfiguration.objects.get(school_id=school_id)
                            votehead_configuration_type = votehead_configuration.configuration_type

                            if votehead_configuration_type == "MANUAL":

                                overpayment_votehead = defaultOverpaymentVoteHead(school_id)
                                if not overpayment_votehead:
                                    transaction.status = "PENDING"
                                    transaction.save()
                                else:

                                    thereceipt = Receipt.objects.create(
                                        school_id=school_id,
                                        student = student,
                                        receipt_date = datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                        receipt_No = receipt_no,
                                        totalAmount = Decimal(amount_paid),
                                        account_type=accounttype,
                                        bank_account = bankAccount,
                                        payment_method = thedefault_MpesaPaymentMethod,
                                        term = term,
                                        year = academic_year,
                                        currency=currency,
                                        transaction_code = transID,
                                        transaction_date = datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                        addition_notes = "Mpesa Payment",
                                        student_class = student.current_Class,
                                        financial_year = financial_year
                                    )

                                    Collection.objects.create(
                                        student = student,
                                        transaction_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                        receipt=thereceipt,
                                        amount = Decimal(amount_paid),
                                        votehead=overpayment_votehead,
                                        school_id=school_id,
                                        is_overpayment = True
                                    )

                                    trackBalance(student,school_id,Decimal(amount_paid),"plus",term,academic_year)

                                    bank_account = bankAccount
                                    amount = thereceipt.totalAmount
                                    initial_balance = bank_account.balance
                                    new_balance = initial_balance + Decimal(amount)
                                    bank_account.balance = new_balance
                                    bank_account.save()

                                    transaction.status = "COMPLETE"
                                    transaction.save()


                            elif votehead_configuration_type == "AUTO":

                                print(f"11111")
                                auto_configuration_type = votehead_configuration.auto_configuration_type

                                student = student
                                voteheads = Invoice.objects.filter(term=term, year=academic_year, school_id=school_id,student=student)

                                if not voteheads:
                                    print(f"1.1.1.1.1")
                                    overpayment_votehead = defaultOverpaymentVoteHead(school_id)
                                    if not overpayment_votehead:
                                        print(f"1.2.2.2.2.2")
                                        transaction.status = "PENDING"
                                        transaction.save()
                                    else:
                                        print(f"1.3.3.3.3")
                                        thereceipt = Receipt.objects.create(
                                            school_id=school_id,
                                            student=student,
                                            receipt_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                            receipt_No=receipt_no,
                                            totalAmount=Decimal(amount_paid),
                                            account_type=accounttype,
                                            bank_account=bankAccount,
                                            payment_method=thedefault_MpesaPaymentMethod,
                                            term=term,
                                            year=academic_year,
                                            currency=currency,
                                            transaction_code=transID,
                                            transaction_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                            addition_notes="Mpesa Payment",
                                            student_class=student.current_Class,
                                            financial_year=financial_year
                                        )

                                        Collection.objects.create(
                                            student=student,
                                            transaction_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                            receipt=thereceipt,
                                            amount=Decimal(amount_paid),
                                            votehead=overpayment_votehead,
                                            school_id=school_id,
                                            is_overpayment=True
                                        )

                                        trackBalance(student, school_id, Decimal(amount_paid), "plus", term, academic_year)


                                        bank_account = bankAccount
                                        amount = thereceipt.totalAmount
                                        initial_balance = bank_account.balance
                                        new_balance = initial_balance + Decimal(amount)
                                        bank_account.balance = new_balance
                                        bank_account.save()

                                        transaction.status = "COMPLETE"
                                        transaction.save()

                                else:
                                    print(f"1.4.4.4.4.4")
                                    votehead_ids = voteheads.values('votehead').distinct()
                                    votehead_objects = VoteHead.objects.filter(id__in=votehead_ids)
                                    totalAmount = Decimal(amount_paid)
                                    numberOfVoteheads = len(votehead_objects)

                                    thereceipt = Receipt.objects.create(
                                        school_id=school_id,
                                        student=student,
                                        receipt_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                        receipt_No=receipt_no,
                                        totalAmount=Decimal(amount_paid),
                                        account_type=accounttype,
                                        bank_account=bankAccount,
                                        payment_method=thedefault_MpesaPaymentMethod,
                                        term=term,
                                        year=academic_year,
                                        currency=currency,
                                        transaction_code=transID,
                                        transaction_date=datetime.strptime(transTime, "%Y%m%d%H%M%S").strftime("%Y-%m-%d"),
                                        addition_notes="Mpesa Payment",
                                        student_class=student.current_Class,
                                        financial_year=financial_year
                                    )

                                    trackBalance(student, school_id, Decimal(amount_paid), "plus", term, academic_year)


                                    overpayment = 0

                                    if auto_configuration_type == RATIO:
                                        print(f"1.5.5.5.5")
                                        eachVoteheadWillGet = totalAmount / numberOfVoteheads
                                        for votehead in votehead_objects:
                                            try:
                                                invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=academic_year,school_id=school_id, student=student)
                                                if (invoice_instance.paid + eachVoteheadWillGet) > invoice_instance.amount:
                                                    print(f"1.6.6.6.6")
                                                    amountRequired = invoice_instance.amount - invoice_instance.paid

                                                    collection_data = {'student': student.id, 'receipt': thereceipt.id, 'amount': amountRequired, 'votehead': votehead.id, 'school_id': school_id}
                                                    collection_serializer = CollectionSerializer(data=collection_data)
                                                    collection_serializer.is_valid(raise_exception=True)
                                                    collection_serializer.save()

                                                    balance = eachVoteheadWillGet - amountRequired
                                                    print(f"balance is {balance}")
                                                    if balance > 0:
                                                        overpayment = overpayment + balance

                                                else:
                                                    print(f"1.7.7.7.7")
                                                    collection_data = {'student': student.id,'receipt': thereceipt.id,'amount': eachVoteheadWillGet,'votehead': votehead.id,'school_id': school_id}
                                                    collection_serializer = CollectionSerializer(data=collection_data)
                                                    collection_serializer.is_valid(raise_exception=True)
                                                    collection_serializer.save()

                                            except Invoice.DoesNotExist:
                                                print(f"1.8.8.8.8")
                                                overpayment += Decimal(amount_paid)
                                            except Invoice.MultipleObjectsReturned:
                                                raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                                    if auto_configuration_type == PRIORITY:
                                        print(f"1.9.9.9.9")
                                        distinct_voteheads = Invoice.objects.filter(term=term, year=academic_year, school_id=school_id, student=student).values_list('votehead', flat=True).distinct()
                                        ordered_voteheads = VoteHead.objects.filter(id__in=distinct_voteheads).order_by(F('priority_number').asc(nulls_first=True))

                                        for index, votehead in enumerate(ordered_voteheads):
                                            print(f"Votehead -> {votehead}, Priority -> {votehead.priority_number}")
                                            if not votehead.is_Overpayment_Default:
                                                print(f"2.0.0.0")
                                                if totalAmount > 0:
                                                    try:
                                                        invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=academic_year, school_id=school_id, student=student)

                                                        if (invoice_instance.paid + totalAmount) > invoice_instance.amount:
                                                            amountRequired = invoice_instance.amount - invoice_instance.paid

                                                            collection_data = {'student': student.id,'receipt': thereceipt.id,'amount': amountRequired,'votehead': votehead.id,'school_id': school_id}
                                                            collection_serializer = CollectionSerializer(data=collection_data)
                                                            collection_serializer.is_valid(raise_exception=True)
                                                            collection_serializer.save()

                                                            totalAmount = totalAmount - amountRequired

                                                            if index == len(voteheads) - 1:
                                                                if totalAmount > 0:
                                                                    overpayment = overpayment + totalAmount

                                                        else:
                                                            collectionAmount = totalAmount
                                                            collection = Collection(student=student, receipt=thereceipt,amount=collectionAmount, votehead=votehead,school_id=school_id)
                                                            collection.save()

                                                            totalAmount = 0.00

                                                    except Invoice.DoesNotExist:
                                                        overpayment += Decimal(amount_paid)
                                                    except Invoice.MultipleObjectsReturned:
                                                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                                    if overpayment > 0:
                                        print(f"2.1.1.1.1")
                                        overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True, school_id=school_id).first()
                                        if not overpayment_votehead:
                                            print(f"2.2.2.2.2")
                                            raise ValueError("Overpayment votehead has not been configured")

                                        newCollection = Collection(student=student,receipt=thereceipt,amount=overpayment,votehead=overpayment_votehead,school_id=school_id.school_id,is_overpayment=True )
                                        newCollection.save()

                                    bank_account = thereceipt.bank_account
                                    amount = thereceipt.totalAmount
                                    initial_balance = bank_account.balance
                                    new_balance = initial_balance + Decimal(amount)
                                    bank_account.balance = new_balance
                                    bank_account.save()


                                    transaction.status = "COMPLETE"
                                    transaction.save()

                                    print(f"2.3.3.3.3")

                        except ObjectDoesNotExist:
                            transaction.status = "PENDING"
                            transaction.save()

        except ObjectDoesNotExist:
            print(f"School is none")
            school = None

        return True




