class AppError(Exception):
    """Base exception for expected application errors."""


class UnsupportedFileTypeError(AppError):
    pass


class FileTooLargeError(AppError):
    pass


class EmptyDocumentError(AppError):
    pass


class SlideNotFoundError(AppError):
    pass


class SlideNotReadyError(AppError):
    pass


class LLMConfigurationError(AppError):
    pass
