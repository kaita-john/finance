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
    currentAcademicYear, currentTerm, defaultAccountType, currentFinancialYear
from voteheads.models import VoteHead
from .models import Grant
from .serializers import GrantSerializer


class GrantCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = GrantSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

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
            if schoolgroup:
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


class GrantListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = GrantSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Grant.objects.none()
        queryset = Grant.objects.filter(school_id=school_id, deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class GrantDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
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













def autoGrant(self, request, school_id, auto_configuration_type, itemamount, bursary, itemstudent,current_financial_year):
    try:
        with transaction.atomic():
            receipt_no = generate_unique_code("RT")
            default_Currency = defaultCurrency(school_id)
            year = currentAcademicYear(school_id)
            term = currentTerm(school_id)
            defaultAccounttype = defaultAccountType(school_id)
            if not default_Currency:
                Response({'detail': "Default Currency Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not year:
                Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not term:
                Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not defaultAccounttype:
                Response({'detail': "Default Account Type Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                bursary = Grant.objects.get(id=bursary)
                itemstudent = Student.objects.get(id = itemstudent)
            except ObjectDoesNotExist:
                raise ValueError("Student or Grant not found")

            itemamount = Decimal(itemamount)
            print(f"Item Amount is {itemamount}")

            receipt_instance = Receipt.objects.create(
                school_id=school_id,
                student=itemstudent,
                receipt_No=receipt_no,
                totalAmount=itemamount,
                account_type=defaultAccounttype,
                bank_account=bursary.bankAccount,
                payment_method=bursary.paymentMethod,
                term=term,
                year=year,
                currency=default_Currency,
                transaction_code=bursary.id,
                addition_notes="Grant Payment",
                financial_year = current_financial_year
            )

            trackBalance(
                receipt_instance.student,
                receipt_instance.school_id,
                receipt_instance.totalAmount,
                "plus",
                receipt_instance.term,
                receipt_instance.year
            )

            receipt_instance.save()



            voteheads = Invoice.objects.filter( term=term, year=year, school_id=school_id, student=itemstudent)
            votehead_ids = voteheads.values('votehead').distinct()
            votehead_objects = VoteHead.objects.filter(id__in=votehead_ids)

            totalAmount = receipt_instance.totalAmount
            numberOfVoteheads = len(votehead_objects)

            overpayment = 0

            if auto_configuration_type == RATIO:
                eachVoteheadWillGet = totalAmount / numberOfVoteheads
                for votehead in votehead_objects:
                    try:
                        invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=year, school_id=school_id, student=itemstudent)
                        if (invoice_instance.paid + eachVoteheadWillGet) > invoice_instance.amount:

                            amountRequired = invoice_instance.amount - invoice_instance.paid
                            collection_data = {'student': itemstudent.id,'receipt': receipt_instance.id,'amount': amountRequired,'votehead': votehead.id,'school_id': school_id,}
                            collection_serializer = CollectionSerializer(data=collection_data)
                            collection_serializer.is_valid(raise_exception=True)
                            collection_serializer.save()

                            balance = eachVoteheadWillGet - amountRequired
                            print(f"balance is {balance}")

                            overpayment = overpayment + balance

                        else:
                            collection_data = {
                                'student': itemstudent.id,
                                'receipt': receipt_instance.id,
                                'amount': eachVoteheadWillGet,
                                'votehead': votehead.id,
                                'school_id': school_id,
                            }
                            collection_serializer = CollectionSerializer(data=collection_data)
                            collection_serializer.is_valid(raise_exception=True)
                            collection_serializer.save()

                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")


            if auto_configuration_type == PRIORITY:
                distinct_voteheads = Invoice.objects.filter(term=term, year=year, school_id=school_id, student=itemstudent) \
                    .values_list('votehead', flat=True) \
                    .distinct()
                ordered_voteheads = VoteHead.objects.filter(id__in=distinct_voteheads) \
                    .order_by(F('priority_number').asc(nulls_first=True))


                for index, votehead in enumerate(ordered_voteheads):
                    print(f"Votehead -> {votehead}, Priority -> {votehead.priority_number}")
                    if not votehead.is_Overpayment_Default:
                        if totalAmount > 0:
                            try:
                                invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=year, school_id=school_id, student=itemstudent)

                                if (invoice_instance.paid + totalAmount) > invoice_instance.amount:
                                    amountRequired = invoice_instance.amount - invoice_instance.paid

                                    collection_data = {
                                        'student': itemstudent.id,
                                        'receipt': receipt_instance.id,
                                        'amount': amountRequired,
                                        'votehead': votehead.id,
                                        'school_id': school_id,
                                    }
                                    collection_serializer = CollectionSerializer(data=collection_data)
                                    collection_serializer.is_valid(raise_exception=True)
                                    collection_serializer.save()

                                    totalAmount = totalAmount - amountRequired
                                    print(f"Total Amount is {totalAmount}")

                                    if index == len(voteheads) - 1:
                                        if totalAmount > 0:
                                            overpayment = overpayment + totalAmount
                                            print(f"Adding overpayment of {overpayment}")

                                else:
                                    collectionAmount = totalAmount
                                    collection = Collection(student = itemstudent,receipt=receipt_instance,amount=collectionAmount,votehead=votehead,school_id=school_id)
                                    collection.save()

                                    totalAmount = 0.00

                            except Invoice.DoesNotExist:
                                pass
                            except Invoice.MultipleObjectsReturned:
                                raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")


            if overpayment > 0:
                overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True).first()
                if not overpayment_votehead:
                    raise ValueError("Overpayment votehead has not been configured")

                newCollection = Collection(
                    student=receipt_instance.student,
                    receipt=receipt_instance,
                    amount=overpayment,
                    votehead=overpayment_votehead,
                    school_id=receipt_instance.school_id,
                    is_overpayment = True
                )
                newCollection.save()

        return Response({'detail': 'Posting Successful! Receipt and collections created successfully'}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)






