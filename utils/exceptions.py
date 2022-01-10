from fastapi import Depends, HTTPException, status

def negative_number_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail = "Negative numbers are not allowed",
        headers = {"X-Error": "Negative number"},
    )
    return exception_response

def bad_request_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail = "Invalid request data.",
        headers = {"X-Error": "Invalid request data"},
    )
    return exception_response

def general_service_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
        detail = "Service unavailable",
        headers = {"X-Error": "Service unavailable", "Retry-After": "10"}
    )
    return exception_response

def database_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
        detail = "Service unavailable",
        headers = {"X-Error": "Service unavailable", "Retry-After": "10"}
    )
    return exception_response

def nasdaq_api_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
        detail = "Service unavailable",
        headers = {"X-Error": "Service unavailable", "Retry-After": "10"}
    )
    return exception_response

def bad_user_create_request_exception():
    exception_response = HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail = "Invalid user data",
        headers = {"X-Error": "Invalid user data"},
    )
    return exception_response


def get_user_exception():
    credential_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentiales",
        headers = {"WWW-Authenticate": "Bearer"}
    )
    return credential_exception


def token_exception():
    token_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Incorrect username or password",
        headers = {"WWW-Authenticate": "Bearer"}
    )
    return token_exception

def symbol_exception():
    token_exception = HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "Symbol not exists",
        headers = {"WWW-Authenticate": "Bearer"}
    )
    return token_exception

def not_available_stock():
    token_exception = HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "Stock not found",
        headers = {"WWW-Authenticate": "Stock not found"}
    )
    return token_exception

def not_enough_stock():
    token_exception = HTTPException(
        status_code = status.HTTP_406_NOT_ACCEPTABLE,
        detail = "There are not enough shares to sell",
        headers = {"WWW-Authenticate": "There are not enough shares to sell"}
    )
    return token_exception

def not_enough_stock_and_pending():
    token_exception = HTTPException(
        status_code = status.HTTP_406_NOT_ACCEPTABLE,
        detail = "There are not enough shares to sell and you have pending purchases to apply",
        headers = {"WWW-Authenticate": "There are not enough shares to sell and you have pending purchases to apply"}
    )
    return token_exception