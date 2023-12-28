from _decimal import Decimal
from django.db.models import Sum

from appcollections.models import Collection
from payment_in_kinds.models import PaymentInKind
from voucher_items.models import VoucherItem


def getBalance(account_type, month, financial_year, school_id):
    if month == 1:
        month = 12
    else:
        month = int(month) - 1

    collectionQuerySet = Collection.objects.filter(
        school_id=school_id,
        receipt__transaction_date__month=month,
        receipt__financial_year=financial_year,
        receipt__account_type=account_type,
    )

    pikQuerySet = PaymentInKind.objects.filter(
        school_id=school_id,
        transaction_date__month=month,
        receipt__financial_year=financial_year,
        receipt__bank_account__account_type=account_type,
    )

    expensesQuerySet = VoucherItem.objects.filter(
        school_id=school_id,
        voucher__paymentDate__month=month,
        voucher__financial_year=financial_year,
        voucher__bank_account__account_type=account_type,
    )

    collectionAmount = collectionQuerySet.aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    pikAmount = pikQuerySet.aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    total_amount = Decimal(collectionAmount) + Decimal(pikAmount)

    collectionQuerySet = list(collectionQuerySet)
    pikQuerySet = list(pikQuerySet)

    cash_at_hand = Decimal(0.0)
    cash_at_bank = Decimal(0.0)

    for collection in collectionQuerySet:
        if collection.receipt.payment_method.is_cash == True:
            cash_at_hand += Decimal(collection.amount)
        elif collection.receipt.payment_method.is_bank == True:
            cash_at_bank += Decimal(collection.amount)

    for pik in pikQuerySet:
        cash_at_hand += Decimal(pik.amoount)

    for voucheritem in expensesQuerySet:
        if voucheritem.receipt.payment_Method.is_cash == True:
            cash_at_hand -= Decimal(voucheritem.amount)
        elif voucheritem.receipt.payment_Method.is_bank == True:
            cash_at_bank -= Decimal(voucheritem.amount)

    return {
        "total": total_amount,
        "cash": cash_at_hand,
        "bank": cash_at_bank,
    }