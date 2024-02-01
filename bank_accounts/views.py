# Create your views here.
import uuid

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from account_types.models import AccountType
from currencies.models import Currency
from utils import SchoolIdMixin, UUID_from_PrimaryKey, DefaultMixin
from .models import BankAccount
from .serializers import BankAccountSerializer


class BankAccountCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school = self.check_school_id(self.request)
        if not school:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        request.data['school'] = school
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school'] = school
            try:
                self.perform_create(serializer)
            except Exception as exception:
                return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'BankAccount created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class BankAccountListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return BankAccount.objects.none()
        queryset = BankAccount.objects.filter(school=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class BankAccountDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return BankAccount.objects.get(id=id)
        except (ValueError, BankAccount.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            account_type_data = request.data.get('account_type', None)
            currency = request.data.get('currency', None)
            if account_type_data:
                account_type = get_object_or_404(AccountType, id=account_type_data)
                serializer.validated_data['account_type'] = account_type
            if currency:
                get_currency = get_object_or_404(Currency, id=currency)
                serializer.validated_data['currency'] = get_currency
            serializer.validated_data['school_id'] = school_id
            try:
                self.perform_update(serializer)
            except Exception as exception:
                return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'BankAccount updated successfully'}, status=status.HTTP_201_CREATED)
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
