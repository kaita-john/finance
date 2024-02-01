# Create your views here.
from collections import defaultdict

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appcollections.models import Collection
from appcollections.serializers import CollectionSerializer
from constants import RATIO, PRIORITY
from grant_items.models import GrantItem
from grant_items.serializers import GrantItemSerializer
from invoices.models import Invoice
from receipts.models import Receipt
from reportss.models import trackBalance
from students.models import Student
from utils import SchoolIdMixin, IsAdminOrSuperUser, UUID_from_PrimaryKey, generate_unique_code, defaultCurrency, \
    currentAcademicYear, currentTerm, defaultAccountType, currentFinancialYear, DefaultMixin
from voteheads.models import VoteHead
from .models import Grant
from .serializers import GrantSerializer


class GrantCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = GrantSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():

            currency = defaultCurrency(school_id)
            if not currency:
                return Response({'detail': f"Default Currency has not been set for this school"}, status=status.HTTP_400_BAD_REQUEST)

            financial_year = currentFinancialYear(school_id)
            if not financial_year:
                return Response({'detail': f"Current Financial Year has not been set for this school"}, status=status.HTTP_400_BAD_REQUEST)


            serializer.validated_data['school_id'] = school_id
            serializer.validated_data['financial_year'] = financial_year

            items_data = serializer.validated_data.pop('items_list', [])

            schoolgroup = serializer.validated_data.get('schoolgroup')
            if schoolgroup and schoolgroup != "null" and schoolgroup != "":
                groupStudents = Student.objects.filter(groups__icontains=str(schoolgroup), school_id=school_id)
                student_ids = [student.id for student in groupStudents]
                serializer.validated_data['students'] = student_ids

            votehead_amounts = defaultdict(Decimal)
            try:
                with transaction.atomic():
                    grant = serializer.save()
                    grant.currency = currency
                    grant.save()

                    print(grant.grant_items)

                    for item in items_data:
                        item['school_id'] = grant.school_id
                        item['grant'] = grant.id
                        grant_itemSerializer = GrantItemSerializer(data=item)
                        grant_itemSerializer.is_valid(raise_exception=True)
                        grant_itemSerializer.save()

                        votehead_id = item['votehead']
                        amount = Decimal(item['amount'])
                        votehead_amounts[votehead_id] += amount

                    assigned_votehead_amounts_serializable = {
                        key: str(value) for key, value in votehead_amounts.items()
                    }
                    grant.assigned_voteheadamounts = dict(assigned_votehead_amounts_serializable)
                    grant.voteheadamounts = dict(assigned_votehead_amounts_serializable)
                    grant.total_amount = grant.overall_amount
                    grant.save()

                    bank_account = grant.bankAccount
                    amount = grant.total_amount
                    initial_balance = bank_account.balance
                    new_balance = initial_balance + Decimal(amount)
                    bank_account.balance = new_balance
                    bank_account.save()


                    return Response({'detail': f'Grant created successfully'},status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("Here")
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GrantListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = GrantSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Grant.objects.none()
        self.check_defaults(self.request, school_id)

        queryset = Grant.objects.filter(school_id=school_id, deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class GrantDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Grant.objects.get(id=id)
        except (ValueError, Grant.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            items_data = serializer.validated_data.get('items_list', [])

            try:
                with transaction.atomic():

                    # Update the grant
                    grant = serializer.save()

                    # Update BankAccount balance
                    bank_account = grant.bankAccount
                    amount = grant.total_amount
                    initial_balance = bank_account.balance
                    new_balance = initial_balance - Decimal(amount)
                    bank_account.balance = new_balance
                    bank_account.save()

                    # Delete existing GrantItems related to the grant
                    GrantItem.objects.filter(grant=instance).delete()

                    # Process GrantItems
                    votehead_amounts = defaultdict(Decimal)
                    for item in items_data:
                        item['school_id'] = grant.school_id
                        item['grant'] = grant.id
                        grant_item_serializer = GrantItemSerializer(data=item)
                        grant_item_serializer.is_valid(raise_exception=True)
                        grant_item_serializer.save()

                        # Calculate votehead amounts
                        votehead_id = item['votehead']
                        amount = Decimal(item['amount'])
                        votehead_amounts[votehead_id] += amount

                    assigned_votehead_amounts_serializable = {
                        key: str(value) for key, value in votehead_amounts.items()
                    }
                    grant.assigned_voteheadamounts = dict(assigned_votehead_amounts_serializable)
                    grant.voteheadamounts = dict(assigned_votehead_amounts_serializable)
                    grant.total_amount = grant.overall_amount

                    grant.save()

                    bank_account = grant.bankAccount
                    amount = grant.total_amount
                    initial_balance = bank_account.balance
                    new_balance = initial_balance + Decimal(amount)
                    bank_account.balance = new_balance
                    bank_account.save()


                    return Response({'detail': 'Grant updated successfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def delete(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        instance = self.get_object()

        if instance.deleted:
            return Response({'detail': f"Grant is already deleted"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                bank_account = instance.bankAccount
                amount = instance.total_amount
                initial_balance = bank_account.balance
                new_balance = initial_balance - Decimal(amount)
                bank_account.balance = new_balance
                bank_account.save()

                instance.deleted = True
                instance.deleted_date = timezone.now()
                instance.save()

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Grant deleted successfully!'}, status=status.HTTP_200_OK)











