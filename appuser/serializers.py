import random
import string

from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from appuser.models import AppUser
from finance import settings
from school.models import School
from school.serializer import SchoolSerializer
from utils import sendMail


class FetchRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'id']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
        }

    def to_internal_value(self, data):
        print('Called')
        roles = []
        if isinstance(data, list):
            role_names = data
        else:
            role_names = [data]
        for role_name in role_names:
            try:
                role = Group.objects.get(name=role_name)
                roles.append(role)
            except Group.DoesNotExist:
                raise ValidationError(f"Role '{role_name}' does not exist.")
        return roles



class AppUserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=False, write_only=True)
    confirmpassword = serializers.CharField(required=False, write_only=True)
    school_id = serializers.UUIDField(required=False)
    roles = FetchRoleSerializer(required=False, many=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'GET':
            self.fields['roles'] = FetchRoleSerializer(many=True)
            self.fields['school_id'] = SchoolSerializer()

    class Meta:
        model = AppUser
        fields = '__all__'

        extra_kwargs = {
            'password': {'write_only': True},
            'confirmpassword': {'write_only': True},
        }



    def create(self, validated_data):
        school_id = validated_data.pop('school_id', None)
        if school_id:
            school = get_object_or_404(School, id=school_id)
            print(f"Found School to be {school} and school_id is {school_id}")
            validated_data['school_id'] = school
        else:
            print("School ID not passed")

        roles_data = validated_data.pop('roles', [])
        roles = FetchRoleSerializer(many=False).to_internal_value(roles_data)

        name = validated_data.pop('first_name', "User")
        sender_email = "kaitaformal@gmail.com"
        sender_password ="wwmx vsyr tvwp sfac"
        receiver_email = validated_data.get('email')
        subject  = "PASSWORD"

        password = validated_data.get('password')
        mypass = None
        if not password:
            if settings.DEBUG:
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                usermessage = f"Dear {name}, thank you for signing up with Finance App. Your password is {password}"
                sendMail(sender_email, sender_password, receiver_email, subject, usermessage)
            else:
                password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
                usermessage = f"Dear {name}, thank you for signing up with Finance App. Your password is {password}"
                sendMail(sender_email, sender_password, receiver_email, subject, usermessage)
            validated_data['password'] = password
            mypass = password

        user = AppUser.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        print(f"roles are {roles}")
        role_ids = [role.id for role in roles]
        print(f"Roles are {role_ids}")
        user.roles.set(role_ids)
        user.save()
        details = {'detail': 'Succeeded', 'mypass': mypass}
        return details


class UpdateAppUserSerializer(serializers.ModelSerializer):
    roles = FetchRoleSerializer(many=False, required=False)
    school_id = serializers.UUIDField(required=False)  # Make school_id optional

    class Meta:
        model = AppUser
        fields = '__all__'

        extra_kwargs = {
            'password': {'write_only': True},
            'confirmpassword': {'write_only': True},
        }

    def update(self, instance, validated_data):
        roles_data = validated_data.pop('roles', [])
        roles = FetchRoleSerializer(many=False).to_internal_value(roles_data)

        instance.phone = validated_data.get('phone', instance.phone)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.is_admin = validated_data.get('is_admin', instance.is_admin)

        # Update roles
        instance.roles.clear()
        role_ids = [role.id for role in roles]
        instance.roles.set(role_ids)

        # Update password if provided
        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        instance.save()
        return instance
