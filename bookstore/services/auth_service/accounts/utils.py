from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        # Flatten nested validation errors into a flat list
        error_messages = []
        if isinstance(errors, dict):
            for field, messages in errors.items():
                if isinstance(messages, list):
                    for msg in messages:
                        if field == 'non_field_errors':
                            error_messages.append(str(msg))
                        else:
                            error_messages.append(f"{field}: {msg}")
                else:
                    error_messages.append(f"{field}: {messages}")
        elif isinstance(errors, list):
            error_messages = [str(e) for e in errors]
        else:
            error_messages = [str(errors)]

        response.data = {
            "success": False,
            "status_code": response.status_code,
            "errors": errors,             # original structure (for form binding)
            "message": error_messages[0] if error_messages else "An error occurred.",
        }

    return response
