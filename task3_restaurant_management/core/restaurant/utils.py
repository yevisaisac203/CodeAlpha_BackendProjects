from rest_framework.response import Response


def success_response(data, message='Success', status=200):
    """
    Return a standardized success response.
    
    Args:
        data: The response data
        message: Optional success message (default: 'Success')
        status: HTTP status code (default: 200)
    
    Returns:
        Response object with standardized format
    """
    return Response({'success': True, 'message': message, 'data': data}, status=status)


def error_response(message, errors=None, status=400):
    """
    Return a standardized error response.
    
    Args:
        message: Error message
        errors: Optional detailed error information
        status: HTTP status code (default: 400)
    
    Returns:
        Response object with standardized format
    """
    return Response({'success': False, 'message': message, 'errors': errors}, status=status)
