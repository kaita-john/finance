# Create your views here.
from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appcollections.models import Collection
from appcollections.serializers import CollectionSerializer
from constants import MANUAL, AUTO, RATIO, PRIORITY
from financial_years.models import FinancialYear
from invoices.models import Invoice
from items.models import Item
from items.serializers import ItemSerializer
from receipts.models import Receipt
from reportss.models import trackBalance
from students.models import Student
from utils import SchoolIdMixin, IsAdminOrSuperUser, UUID_from_PrimaryKey, generate_unique_code, defaultCurrency, \
    currentAcademicYear, currentTerm, defaultAccountType
from voteheads.models import VoteheadConfiguration, VoteHead
from .models import Bursary
from .serializers import BursarySerializer


class BursaryCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = BursarySerializer
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

            serializer.validated_data['school_id'] = school_id

            schoolgroup = serializer.validated_data.get('schoolgroup')
            studentamount = serializer.validated_data.get('studentamount')

            items_data = serializer.validated_data.pop('items_list', [])

            if schoolgroup:
                if not studentamount:
                    return Response({'detail': f"Enter amount for each student"}, status=status.HTTP_400_BAD_REQUEST)

                groupStudents = Student.objects.filter(group = schoolgroup, school_id=school_id)
                for value in groupStudents:
                    item = {'amount': studentamount, 'student': value.id}
                    items_data.append(item)

            try:
                with transaction.atomic():
                    busary = serializer.save()
                    busary.currency = currency
                    busary.save()

                    for item in items_data:
                        item['school_id'] = busary.school_id
                        item['bursary'] = busary.id
                        itemSerializer = ItemSerializer(data=item)
                        itemSerializer.is_valid(raise_exception=True)
                        saved_item = itemSerializer.save()

                        item_instance = get_object_or_404(Item, id=saved_item.id)
                        student_instance = item_instance.student
                        if isinstance(student_instance, Student):
                            item_instance.student_class = student_instance.current_Class
                            item_instance.save()

                    return Response({'detail': f'Bursary created successfully'},status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("Here")
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BursaryListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Bursary.objects.none()
        queryset = Bursary.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class BursaryDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Bursary.objects.get(id=id)
        except (ValueError, Bursary.DoesNotExist):
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

            Item.objects.filter(bursary=instance).delete()
            bursary = serializer.save()

            items_data = serializer.validated_data.get('items_list', [])
            for item in items_data:
                item['school_id'] = bursary.school_id
                item['bursary'] = bursary.id
                itemSerializer = ItemSerializer(data=item)
                itemSerializer.is_valid(raise_exception=True)
                saved_item = itemSerializer.save()

                item_instance = get_object_or_404(Item, id=saved_item.id)
                student_instance = item_instance.student
                if isinstance(student_instance, Student):
                    item_instance.student_class = student_instance.current_Class
                    item_instance.save()

            self.perform_update(serializer)

            return Response({'detail': 'Bursary updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def delete(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Bursary deleted successfully!'}, status=status.HTTP_200_OK)














def autoBursary(self, request, school_id, auto_configuration_type, itemamount, bursary, itemstudent,current_financial_year):
    try:
        with transaction.atomic():
            receipt_no = generate_unique_code("RT")
            default_Currency = defaultCurrency(school_id)
            year = currentAcademicYear()
            term = currentTerm()
            defaultAccounttype = defaultAccountType()
            if not default_Currency:
                Response({'detail': "Default Currency Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not year:
                Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not term:
                Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not defaultAccounttype:
                Response({'detail': "Default Account Type Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                bursary = Bursary.objects.get(id=bursary)
                itemstudent = Student.objects.get(id = itemstudent)
            except ObjectDoesNotExist:
                raise ValueError("Student or Bursary not found")

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
                addition_notes="Bursary Payment",
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




class PostBursaryDetailView(SchoolIdMixin, generics.UpdateAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        partial = kwargs.pop('partial', False)
        bursary = self.get_object()

        if bursary.posted:
            return Response({'detail': "Bursary has already been posted"}, status=status.HTTP_400_BAD_REQUEST)

        bursary.posted = True
        bursary.save()

        serializer = self.get_serializer(bursary, data=request.data, partial=partial)
        if serializer.is_valid():
            print(f"22222222")
            items_data = serializer.get_items(bursary)
            print(f"Items data is {items_data}")
            if not items_data:
                return Response({'detail': "Bursay has zero items"}, status=status.HTTP_400_BAD_REQUEST)
            for item in items_data:
                print(f"4444444")
                print(f"Item is {item}")
                itemamount = item.get('amount')
                bursary  = item.get('bursary')
                itemstudent = item.get('student')

                try:
                    print(f"5555555555")
                    configuration = VoteheadConfiguration.objects.get(school_id=school_id)
                    print("returning 2")
                except ObjectDoesNotExist:
                    print("returning 3")
                    return Response({'detail': "Please set up votehead configuration for this school first!"},status=status.HTTP_400_BAD_REQUEST)

                print(f"66666666666")
                configuration_type = configuration.configuration_type
                auto_configuration_type = configuration.auto_configuration_type

                try:
                    current_financial_year = FinancialYear.objects.get(is_current=True, school=school_id)
                except ObjectDoesNotExist:
                    return Response({'detail': f"Current Financial Year not set"}, status=status.HTTP_400_BAD_REQUEST)


                if configuration_type == MANUAL:
                    print("returning 4")
                    return Response({'detail': "Votehead Configuration set to manual. Change to Auto"}, status=status.HTTP_400_BAD_REQUEST)
                elif configuration_type == AUTO:
                    print("returning 5")
                    print(f"Item bursary is {bursary}")
                    return autoBursary(self, request, school_id, auto_configuration_type, itemamount, bursary, itemstudent, current_financial_year)

                return JsonResponse({'detail': 'Invalid request'}, status=400)

        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UnPostBursaryDetailView(SchoolIdMixin, generics.UpdateAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        bursary = self.get_object()

        if not bursary.posted:
            return Response({'detail': "This bursary is already unposted"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            bursary.posted = False
            bursary.unposted_date = datetime.now()
            bursary.save()

            receipts = Receipt.objects.filter(is_reversed = False, school_id=school_id, transaction_code = bursary.id)
            for receipt in receipts:
                receipt.is_reversed = True
                receipt.reversal_date = datetime.now()
                receipt.save()

                receipt_instance = receipt
                trackBalance(
                    receipt_instance.student,
                    receipt_instance.school_id,
                    receipt_instance.totalAmount,
                    "minus",
                    receipt_instance.term,
                    receipt_instance.year
                )

        return Response({'detail': "Bursary has been unposted successfully"}, status=status.HTTP_200_OK)
