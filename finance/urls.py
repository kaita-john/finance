from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from finance import settings

api_version = 'api/v1/'

api_patterns = [
    path(api_version + 'users/', include('appuser.urls')),
    path(api_version + 'schools/', include('school.urls')),
    path(api_version + 'admin/academics/', include('academic_year.urls')),
    path(api_version + 'admin/financials/', include('financial_years.urls')),
    path(api_version + 'admin/groups/', include('schoolgroups.urls')),
    path(api_version + 'admin/terms/', include('term.urls')),
    path(api_version + 'admin/classes/', include('classes.urls')),
    path(api_version + 'admin/streams/', include('streams.urls')),
    path(api_version + 'admin/currencies/', include('currencies.urls')),
    path(api_version + 'admin/invoices/', include('invoices.urls')),
    path(api_version + 'admin/feestructures/', include('fee_structures.urls')),
    path(api_version + 'admin/fee-structure-items/', include('fee_structures_items.urls')),
    path(api_version + 'admin/payment-methods/', include('payment_methods.urls')),
    path(api_version + 'accounting/account-types/', include('account_types.urls')),
    path(api_version + 'accounting/voteheads/', include('voteheads.urls')),
    path(api_version + 'master/schooltypes/', include('school_types.urls')),
    path(api_version + 'master/schoolcategories/', include('school_categories.urls')),
    path(api_version + 'accounting/bank-accounts/', include('bank_accounts.urls')),
    path(api_version + 'superadmin/roles/', include('roles.urls')),
    path(api_version + 'files/', include('file_upload.urls')),
    path(api_version + 'web/', include('web.urls')),
    path(api_version + 'receipts/', include('receipts.urls')),
    path(api_version + 'receipts/', include('receipts.urls')),
    path(api_version + 'bursaries/', include('bursaries.urls')),
    path(api_version + 'items/', include('items.urls')),


    path(api_version + 'admin/suppliers/', include('suppliers.urls')),
    path(api_version + 'admin/staff/', include('staff.urls')),
    path(api_version + 'admin/expense-categories/', include('expense_categories.urls')),

    path(api_version + 'vouchers/', include('vouchers.urls')),
    path(api_version + 'vouchers/voucher-items', include('voucher_items.urls')),
    path(api_version + 'vouchers/voucher-attatchments', include('voucher_attatchments.urls')),

    path(api_version + 'collections/', include('appcollections.urls')),
    path(api_version + 'paymentinkind/', include('payment_in_kind_Receipt.urls')),
    path(api_version + 'students/', include('students.urls')),
    path('accounts/', include('allauth.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('', include('appuser.urls')),
]

urlpatterns = api_patterns + [
    path('admin/', admin.site.urls),
]


