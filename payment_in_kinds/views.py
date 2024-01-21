# Create your views here.
import uuid

from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice
from utils import SchoolIdMixin, IsAdminOrSuperUser, generate_unique_code
from .models import PaymentInKind
from .serializers import PaymentInKindSerializer


class PaymentInKindCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = PaymentInKindSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        amount = request.data.get('amount')
        student = request.data.get('student')
        term = request.data.get('term')
        year = request.data.get('year')
        votehead = request.data.get('votehead')

        try:
            invoice = Invoice.objects.filter(term=term,year=year,student_id=student,school_id=school_id, votehead=votehead).first()
            with transaction.atomic():
                if invoice:
                    invoice.paid += amount
                    invoice.due = invoice.amount - invoice.paid
                    invoice.save()

                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid():
                    serializer.validated_data['school_id'] = school_id
                    serializer.validated_data['receipt_no'] = generate_unique_code("COL")
                    serializer.save()
                    return Response({'detail': 'PaymentInKind created successfully'}, status=status.HTTP_201_CREATED)
                else:
                    return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentInKindListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = PaymentInKindSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return PaymentInKind.objects.none()
        queryset = PaymentInKind.objects.filter(school_id=school_id).order_by('-transaction_date')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class PaymentInKindDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = PaymentInKind.objects.all()
    serializer_class = PaymentInKindSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]


    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id =  uuid.UUID(primarykey)
            return PaymentInKind.objects.get(id=id)
        except (ValueError, PaymentInKind.DoesNotExist):
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
            self.perform_update(serializer)
            return Response({'detail': 'Fee Structure Item updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Record deleted successfully'}, status=status.HTTP_200_OK)




class OverpaymentPaymentInKindListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = PaymentInKindSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return PaymentInKind.objects.none()
        queryset = PaymentInKind.objects.filter(school_id=school_id, votehead__is_Overpayment_Default=True, receipt__is_posted = True).order_by('-transaction_date')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

