
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response and 'detail' in response.data:
        response.data['detail'] = response.data.pop('detail')

    return response