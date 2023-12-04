from django.contrib import admin
from django.urls import path, include

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
    path(api_version + 'accounting/account-types/', include('account_types.urls')),
    path(api_version + 'accounting/voteheads/', include('voteheads.urls')),
    path(api_version + 'master/schooltypes/', include('school_types.urls')),
    path(api_version + 'master/schoolcategories/', include('school_categories.urls')),
    path(api_version + 'accounting/bank-accounts/', include('bank_accounts.urls')),
    path(api_version + 'superadmin/roles/', include('roles.urls')),
    path(api_version + 'students/', include('students.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('appuser.urls')),
]

urlpatterns = api_patterns + [
    path('admin/', admin.site.urls),
]


