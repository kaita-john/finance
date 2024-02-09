# Create your views here.
from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F, Sum
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
    currentAcademicYear, currentTerm, defaultAccountType, DefaultMixin, defaultBursaryVoteHead
from voteheads.models import VoteheadConfiguration, VoteHead
from voucher_items.models import VoucherItem
from vouchers.models import Voucher
from .models import Bursary
from .serializers import BursarySerializer



class BursaryCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = BursarySerializer
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

            votehead = defaultBursaryVoteHead(school_id)
            if not votehead:
                return Response({'detail': f"Default Bursary VoteHead has not been set for this school"}, status=status.HTTP_400_BAD_REQUEST)

            serializer.validated_data['school_id'] = school_id
            serializer.validated_data['votehead'] = votehead

            schoolgroup = serializer.validated_data.get('schoolgroup')
            classes = serializer.validated_data.get('classes')
            studentamount = serializer.validated_data.get('studentamount')

            items_data = serializer.validated_data.pop('items_list', [])

            if schoolgroup and schoolgroup != "" and schoolgroup != "null":
                if not studentamount or studentamount == "" or studentamount == "null":
                    return Response({'detail': f"Enter amount for each student"}, status=status.HTTP_400_BAD_REQUEST)
                if classes and classes != "" and classes != "null":
                    return Response({'detail': f"You cannot select both Classes and School"}, status=status.HTTP_400_BAD_REQUEST)
                groupStudents = Student.objects.filter(groups__icontains=str(schoolgroup), school_id=school_id)
                for value in groupStudents:
                    item = {'amount': studentamount, 'student': value.id}
                    items_data.append(item)

            if classes and classes != "" and classes != "null":
                if schoolgroup and schoolgroup != "" and schoolgroup != "null":
                    return Response({'detail': f"You cannot select both Classes and School"}, status=status.HTTP_400_BAD_REQUEST)
                if not studentamount or studentamount == "" or studentamount == "null":
                    return Response({'detail': f"Enter amount for each student"}, status=status.HTTP_400_BAD_REQUEST)
                classesStudents = Student.objects.filter(current_Class=classes, school_id=school_id)
                for value in classesStudents:
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


class BursaryListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        self.check_defaults(self.request, school_id)

        if not school_id:
            return Bursary.objects.none()
        self.check_defaults(self.request, school_id)
        queryset = Bursary.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class BursaryDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
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
        self.check_defaults(self.request, school_id)

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
        self.check_defaults(self.request, school_id)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Bursary deleted successfully!'}, status=status.HTTP_200_OK)














def autoBursary(self, request, school_id, auto_configuration_type, itemamount, bursary, itemstudent,current_financial_year):
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
                transaction_code=receipt_no,
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

            # print("Here  2")
            # bank_account = receipt_instance.bank_account
            # amount = receipt_instance.totalAmount
            # initial_balance = bank_account.balance
            # new_balance = initial_balance + Decimal(amount)
            # bank_account.balance = new_balance
            # bank_account.save()

            overpayment = 0
            totalAmount = receipt_instance.totalAmount

            voteheads = Invoice.objects.filter( term=term, year=year, school_id=school_id, student=itemstudent)

            if not voteheads:
                overpayment += totalAmount

            else:
                votehead_ids = voteheads.values('votehead').distinct()
                votehead_objects = VoteHead.objects.filter(id__in=votehead_ids)
                numberOfVoteheads = len(votehead_objects)

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
                overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True, school_id = school_id).first()
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

            bursary.posted = True
            bursary.save()

    except ValueError as e:
        raise ValueError({'detail': str(e)})




class PostBursaryDetailView(SchoolIdMixin, DefaultMixin, generics.UpdateAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        try:
            partial = kwargs.pop('partial', False)
            bursary = self.get_object()

            if bursary.posted:
                return Response({'detail': "Bursary has already been posted"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(bursary, data=request.data, partial=partial)
            if serializer.is_valid():

                with transaction.atomic():

                    bursary_total_amount = bursary.items.aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal(0)
                    actualvotehead = bursary.votehead

                    voucher_instance = Voucher.objects.create(
                        school_id=school_id,
                        accountType=bursary.bankAccount.account_type,
                        recipientType="other",
                        other=f"BURSARY",
                        bank_account=bursary.bankAccount,
                        payment_Method=bursary.paymentMethod,
                        referenceNumber=str(bursary.id),
                        paymentDate=bursary.receipt_date,
                        description="AUTO PIK",
                        totalAmount=bursary_total_amount,
                        deliveryNoteNumber="AUTO",
                        financial_year=bursary.financial_year,
                    )

                    VoucherItem.objects.create(
                        voucher=voucher_instance,
                        school_id=school_id,
                        votehead=actualvotehead,
                        amount=bursary_total_amount,
                        quantity=Decimal(1),
                        itemName="Bursary",
                    )

                    print(f"22222222")
                    items_data = serializer.get_items(bursary)
                    print(f"Items data is {items_data}")
                    if not items_data:
                        return Response({'detail': "Bursay has zero items"}, status=status.HTTP_400_BAD_REQUEST)
                    print(f'Length of items_data is {len(items_data)}')
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
                            autoBursary(self, request, school_id, auto_configuration_type, itemamount, bursary, itemstudent, current_financial_year)

                return Response({'detail': f"Posting Successful! Receipt and collections created successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class UnPostBursaryDetailView(SchoolIdMixin, DefaultMixin, generics.UpdateAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

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

                # bank_account = receipt_instance.bank_account
                # amount = receipt_instance.totalAmount
                # initial_balance = bank_account.balance
                # new_balance = initial_balance - Decimal(amount)
                # bank_account.balance = new_balance
                # bank_account.save()

                try:
                    related_voucher = Voucher.objects.get(referenceNumber=bursary.id)
                    related_voucher.is_deleted = True
                except ObjectDoesNotExist:
                    voucher = None


        return Response({'detail': "Bursary has been unposted successfully"}, status=status.HTTP_200_OK)




class TrashBursaryDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Bursary.objects.all()
    serializer_class = BursarySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    lookup_field = 'pk'


    def destroy(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        bursary = self.get_object()
        if bursary.posted:
            return Response({'detail': f"You cannot delete a posted Bursary, Unpost it instead"}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(bursary)
        return Response({'detail': 'Record deleted successfully'}, status=status.HTTP_200_OK)


