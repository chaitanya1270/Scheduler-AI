from fastapi import HTTPException
from fastapi.responses import JSONResponse
import traceback


def get_exception_info(exception, max_traceback_size=10):
    # Get the exception type and message
    exception_type = type(exception).__name__
    exception_message = str(exception)

    # Get the stack trace
    traceback_list = traceback.format_exc().strip().split("\n")
    traceback_list = traceback_list[-max_traceback_size:]

    exception_info = {
        "Exception Type": exception_type,
        "Exception Message": exception_message,
        "Stack Trace": traceback_list
        # Add any other relevant information here
    }

    return exception_info


class ApiResponse:

    @staticmethod
    def response_created(
        data,
        status="SUCCESS",
        display_message="Resource created",
        code=201,
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": data,
            "error": {},
        }
        return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_ok(
        data,
        code=200,
        status="SUCCESS",
        display_message="",
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": data,
            "error": {},
        }
        return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_internal_server_error(
        exception, 
        code=500, 
        status="ERROR", 
        display_message=""
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
        return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_bad_request(
        exception, 
        code=500, 
        status="ERROR", 
        display_message=""
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
        return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_unprocessable_entity(
        exception, 
        code=422, 
        status="FAIL", 
        display_message=""
    ):
       data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
       return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_conflict(
        exception, 
        code=409, 
        status="FAIL", 
        display_message=""
    ):
       data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
       return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_unauthenticate(
        exception, 
        code=401, 
        status="FAIL", 
        display_message=""
    ):
       data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
       return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_unauthorized(
        exception, 
        code=403, 
        status="FAIL", 
        display_message=""
    ):
       data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
       return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_not_found(
        exception, 
        code=404, 
        status="FAIL", 
        display_message=""
    ):
       data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
       return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_not_acceptable(
        exception, 
        code=406, 
        status="FAIL", 
        display_message=""
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
        return JSONResponse(content=data, status_code=code)

    @staticmethod
    def response_conflict_request(
        exception, 
        code=409, 
        status="FAIL", 
        display_message=""
    ):
        data = {
            "display_message": display_message,
            "status": status,
            "data": {},
            "error": get_exception_info(exception),
        }
        return JSONResponse(content=data, status_code=code)
