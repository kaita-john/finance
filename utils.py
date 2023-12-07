import os
import smtplib
import uuid
from datetime import datetime

import jwt
from django.contrib.auth.models import Group
from rest_framework import permissions
from django.db import models
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import ValidationError

from academic_year.models import AcademicYear
from finance.settings import SIMPLE_JWT
from school.models import School
import time

from term.models import Term


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
        return request.user and (request.user.is_admin or IsAdminUser().has_permission(request, view) or IsSuperUser().has_permission(request, view))


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

    upload_to = f"{str(now.year)}/{month}/{day}/{hour}"
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid.uuid4().hex, ext)
    return os.path.join(upload_to, filename)


def currentAcademicYear():
    try:
        return AcademicYear.objects.get(is_current=True)
    except AcademicYear.DoesNotExist:
        return None


def currentTerm():
    try:
        return Term.objects.get(is_current=True)
    except Term.DoesNotExist:
        return None