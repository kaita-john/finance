import base64
import math
import time
from datetime import datetime

import requests
from phonenumber_field.phonenumber import PhoneNumber
from requests.auth import HTTPBasicAuth
from rest_framework import serializers
from rest_framework.response import Response

from mpesa_configs.models import Mpesaconfig
from students.models import Student
from transactions.models import Transaction


class Decorators:
    @staticmethod
    def refresh_token(decorated):
        def wrapper(gateway, *args, **kwargs):
            if (
                    gateway.access_token_expiration
                    and time.time() > gateway.access_token_expiration
            ):
                token = gateway.get_access_token()
                gateway.access_token = token
            return decorated(gateway, *args, **kwargs)

        return wrapper


class MpesaGateway:
    shortcode = None
    consumer_key = None
    consumer_secret = None
    access_token_url = None
    access_token = None
    access_token_expiration = None
    checkout_url = None
    timestamp = None

    def __init__(self, school_id):
        configurations = Mpesaconfig.objects.filter(school_id = school_id)

        if configurations.exists():
            configuration = configurations.first()

            self.headers = None
            self.access_token_expiration = None
            self.password = self.generate_password()

            self.shortcode = configuration.shortcode
            self.consumer_key = configuration.consumer_key
            self.consumer_secret = configuration.consumer_secret
            self.access_token_url = configuration.access_token_url
            self.checkout_url = configuration.checkout_url
            self.passkey = configuration.passkey
            self.callback_url = configuration.callback_url

            try:
                self.access_token = self.get_access_token()
                if self.access_token is None:
                    raise Exception("Request for access token failed.")
            except Exception as e:
                pass
            else:
                self.access_token_expiration = time.time() + 3400

        else:
            raise ValueError(f"No Mpesa Config found for school_id {school_id}")




    def generate_password(self):
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"TIME IS {self.timestamp} and self.shortcode is {self.shortcode}")
        password = self.shortcode + self.passkey + self.timestamp
        password_byte = password.encode("ascii")
        return base64.b64encode(password_byte).decode("utf-8")


    def getStudent(self):
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"TIME IS {self.timestamp} and self.shortcode is {self.shortcode}")
        password = self.shortcode + self.passkey + self.timestamp
        password_byte = password.encode("ascii")
        return base64.b64encode(password_byte).decode("utf-8")

    def get_access_token(self):
        try:
            res = requests.get(self.access_token_url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret))
        except Exception as e:
            raise e

        token = res.json()['access_token']
        self.headers = {"Authorization": "Bearer %s" % token}
        return token

    @Decorators.refresh_token
    def stk_push_request(self, amount, mobile, admissionnumber, school_id, purpose, timestamp):
        try:
            student = Student.objects.get(admission_number=admissionnumber, school_id=school_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError(f"Student with the  Admission Number {admissionnumber}  does not exist")

        body = {
            "BusinessShortCode": self.shortcode,
            "Password": self.password,
            "Timestamp": self.timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": math.ceil(float(amount)),
            "PartyA": mobile,
            "PartyB": self.shortcode,
            "PhoneNumber": mobile,
            "CallBackURL": self.callback_url,
            "AccountReference": str(mobile),
            "TransactionDesc": str(mobile),
            "headers": self.headers
        }

        try:
            res = requests.post(self.checkout_url, json=body, headers=self.headers, timeout=30)
            res_data = res.json()
            print("HERE 1" + str(res_data))

            if res.ok:
                transaction = Transaction.objects.create(
                    mobile = mobile,
                    amount = amount,
                    student = student,
                    school_id = school_id,
                    purpose = purpose,
                    checkoutid=res_data["CheckoutRequestID"],
                    timestamp=timestamp
                )
                transaction.save()

                data = {}
                data['details'] = "Successful"
                return Response(data)

            else:
                print("HERE 2    " + str(res_data))
                raise Exception(f"{str(res_data['errorMessage'])}")
        except Exception as e:
            raise Exception(e)




    @staticmethod
    def check_status(data):
        try:
            status = data["Body"]["stkCallback"]["ResultCode"]
        except Exception as e:
            status = 1
        return status

    @staticmethod
    def getTransactionObjectWithSimilarCheckoutRequestId(data):
        checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
        transaction, _ = Transaction.objects.get_or_create(checkoutid=checkout_request_id)
        return transaction



    def callback(self, data):
        status = self.check_status(data)
        transaction = self.getTransactionObjectWithSimilarCheckoutRequestId(data)

        if not transaction:
            checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
            raise Exception(f"Transaction with reference Id {checkout_request_id} not found!")

        amount = 0
        phone_number = 0
        receiptnumber = 0
        if status == 0:
            items = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
            for item in items:
                if item["Name"] == "Amount":
                    amount = item["Value"]
                elif item["Name"] == "MpesaReceiptNumber":
                    receiptnumber = item["Value"]
                elif item["Name"] == "PhoneNumber":
                    phone_number = item["Value"]

            if  transaction.purpose == "SCHOOLFEES":
                student = transaction.student

                # userpaid = amount
                # minutespershilling = Constant.objects.get(school=student.school).minutepershilling
                # minutespertokenOrequivalentminutes = Constant.objects.get(school=student.school).minutespertokenOrequivalentminutes
                # minutespertokenOrequivalentminutes = Constant.objects.get(school=student.school).minutespertokenOrequivalentminutes
                # shillingspertokenOrequivalentshillings = Constant.objects.get(school=student.school).shillingspertokenOrequivalentshillings
                # # SUBTRACT TOKENS AND MINUTES FROM USER
                #
                # student.tokenbalance = student.tokenbalance + (userpaid / shillingspertokenOrequivalentshillings)
                # print(f"Student token balance is {student.tokenbalance} and userpaid {userpaid}  and shillings per token is {shillingspertokenOrequivalentshillings} so new token is {student.tokenbalance + (userpaid / shillingspertokenOrequivalentshillings)}")
                # student = transaction.student
                # student.save()
                #
                # school = student.school
                #
                # listOfMobiles = Mobile.objects.filter(school = school)
                # numberOfPhones = len(listOfMobiles)
                # shillingsPaidPerMobile = userpaid / numberOfPhones
                # tokensToBeDeductedPerMobile = shillingsPaidPerMobile / shillingspertokenOrequivalentshillings
                #
                # for mobile in listOfMobiles:
                #     mobile.standingtoken -= tokensToBeDeductedPerMobile
                #     mobile.standingminutes -= (shillingsPaidPerMobile * minutespershilling)
                #     mobile.save()
                #     print(f"ALSO FOUND {student.fullname} - {school.name} - {mobile}")

            user =  transaction.user
            if user:
                user.is_active = True
                user.save()

            transaction.amount = amount
            transaction.reference = receiptnumber
            transaction.mobile = PhoneNumber(raw_input=phone_number)
            transaction.receiptnumber = receiptnumber
            transaction.status = "COMPLETE"


        elif status == 1032:
            transaction.status = "CANCELLED"
        else:
            transaction.status = "FAILED"


        transaction.save()
        return True











    def callback(self, data):
        status = self.check_status(data)
        transaction = self.getTransactionObjectWithSimilarCheckoutRequestId(data)

        if not transaction:
            checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
            raise Exception(f"Transaction with reference Id {checkout_request_id} not found!")