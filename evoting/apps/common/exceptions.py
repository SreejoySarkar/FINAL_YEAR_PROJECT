from rest_framework.exceptions import APIException


class ApiError(APIException):
    """Uniform error body: {"code": "SOME_CODE", "message": "human readable"}."""

    status_code = 400

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.status_code = status_code
        self.code = code
        super().__init__(detail={"code": code, "message": message})
