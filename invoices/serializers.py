from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from currencies.serializers import CurrencySerializer
from streams.serializers import StreamsSerializer
from students.serializers import StudentSerializer
from term.serializers import TermSerializer
from .models import Invoice, Structure, Uninvoice


class InvoiceSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', required=False, read_only=True)
    term_details  = TermSerializer(source='term', required=False, read_only=True)
    currency_details  = CurrencySerializer(source='currency', required=False, read_only=True)
    class Meta:
        model = Invoice
        fields = '__all__'


class StructureSerializer(serializers.ModelSerializer):
    structure_year_details = AcademicYearSerializer(source='structure_year', required=False, read_only=True)
    structure_class_details = ClassesSerializer(source='structure_class', required=False, read_only=True)
    structure_term_details = TermSerializer(source='structure_term', required=False, read_only=True)
    student_details = StudentSerializer(source='student', required=False, read_only=True)
    classes_details = ClassesSerializer(source='classes', required=False, read_only=True)
    stream_details = StreamsSerializer(source='stream', required=False, read_only=True)
    class Meta:
        model = Structure
        fields = '__all__'


class UninvoiceStudentSerializer(serializers.ModelSerializer):
    structure_year_details = AcademicYearSerializer(source='structure_year', required=False, read_only=True)
    structure_class_details = ClassesSerializer(source='structure_class', required=False, read_only=True)
    structure_term_details = TermSerializer(source='structure_term', required=False, read_only=True)
    class Meta:
        model = Uninvoice
        fields = '__all__'