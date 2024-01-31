# Create your views here.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tespython import MpesaInit
from utils import SchoolIdMixin, UUID_from_PrimaryKey
from .models import Mpesaconfig
from .serializers import MpesaconfigSerializer


class MpesaconfigCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = MpesaconfigSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            existing_instances = Mpesaconfig.objects.count()
            if existing_instances >= 1:
                return Response({'detail': f"Mpesaconfig already saved. Edit existing configuration"}, status=status.HTTP_400_BAD_REQUEST)

            self.perform_create(serializer)
            return Response({'detail': 'Mpesaconfig created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class MpesaconfigListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = MpesaconfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Mpesaconfig.objects.none()
        queryset = Mpesaconfig.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)


class MpesaconfigDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Mpesaconfig.objects.all()
    serializer_class = MpesaconfigSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Mpesaconfig.objects.get(id=id)
        except (ValueError, Mpesaconfig.DoesNotExist):
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
            return Response({'detail': 'Mpesaconfig updated successfully'}, status=status.HTTP_201_CREATED)
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






class MpesaCallBackView(APIView):
    @csrf_exempt
    def post(self, request):
        data = request.data
        mpesa = MpesaInit(None)

        try:
            mpesa.callback(data)
        except Exception as e:
            print(f"Exception: {e}")

        if mpesa:
            return Response({"details": "Success"}, status=status.HTTP_200_OK)
        return Response({"details": "Failed"}, status=status.HTTP_400_BAD_REQUEST)





class RegisterMpesaValidationandCallBackView(SchoolIdMixin, APIView):
    @csrf_exempt
    def post(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        mpesa = MpesaInit(school_id)

        try:
            mpesa.register_confirmation_and_validation_url()
            print(f"registered successfully")
        except Exception as exception:
            return Response({'detail': exception}, status=status.HTTP_400_BAD_REQUEST)

        if mpesa:
            return Response({"details": "Success"}, status=status.HTTP_200_OK)
        return Response({"details": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
