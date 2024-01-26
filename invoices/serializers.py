from _decimal import Decimal
from django.db.models import Sum
from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from appcollections.models import Collection
from classes.serializers import ClassesSerializer
from currencies.serializers import CurrencySerializer
from receipts.models import Receipt
from school.models import School
from school.serializer import SchoolSerializer
from schoolgroups.serializers import SchoolGroupSerializer
from streams.serializers import StreamsSerializer
from students.serializers import StudentSerializer
from term.serializers import TermSerializer
from .models import Invoice, Structure, Uninvoice, Balance


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = '__all__'



class InvoiceSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', required=False, read_only=True)
    term_details  = TermSerializer(source='term', required=False, read_only=True)
    currency_details  = CurrencySerializer(source='currency', required=False, read_only=True)
    paid = serializers.SerializerMethodField(read_only=True)
    due = serializers.SerializerMethodField(read_only=True)

    def get_paid(self, obj):
        invoice = obj
        try:
            school = School.objects.get(id=invoice.student.school_id)
            student = invoice.student
            term = invoice.term
            year = invoice.year
            voteheads = invoice.votehead

            total_amount_paid = Collection.objects.filter(
                votehead=voteheads,
                student=student,
                receipt__term=term,
                receipt__year=year,
                receipt__is_reversed=False,
                school_id= school.id
            ).aggregate(total_amount_paid=Sum('amount'))['total_amount_paid'] or 0.0

            return total_amount_paid

        except School.DoesNotExist:
            return {'error': f"School not found"}
        except Exception as exception:
            return {'error': f"Bad Request {exception}"}

    def get_due(self, obj):
        invoice = obj
        try:
            school = School.objects.get(id=invoice.student.school_id)
            student = invoice.student
            term = invoice.term
            year = invoice.year
            voteheads = invoice.votehead
            amountRequired = invoice.amount

            total_amount_paid = Collection.objects.filter(
                votehead=voteheads,
                student=student,
                receipt__term=term,
                receipt__year=year,
                receipt__is_reversed=False,
                school_id= school.id
            ).aggregate(total_amount_paid=Sum('amount'))['total_amount_paid'] or 0.0

            return amountRequired - Decimal(total_amount_paid)

        except School.DoesNotExist:
            return {'error': f"School not found"}
        except Exception as exception:
            return {'error': f"Bad Request {exception}"}

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
    group_details = SchoolGroupSerializer(source='group', required=False, read_only=True)
    class Meta:
        model = Structure
        fields = '__all__'


class UninvoiceStudentSerializer(serializers.ModelSerializer):
    structure_year_details = AcademicYearSerializer(source='structure_year', required=False, read_only=True)
    structure_class_details = ClassesSerializer(source='structure_class', required=False, read_only=True)
    structure_term_details = TermSerializer(source='structure_term', required=False, read_only=True)
    structure_stream_details = StreamsSerializer(source='structure_stream', required=False, read_only=True)  # Corrected here
    student_details = StudentSerializer(source='student', required=False, read_only=True)

    class Meta:
        model = Uninvoice
        fields = '__all__'
