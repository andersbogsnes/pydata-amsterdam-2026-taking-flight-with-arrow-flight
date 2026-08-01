import logging

import structlog


def configure_logging(is_dev: bool = True) -> None:
    shared_processors = [structlog.contextvars.merge_contextvars,
                         structlog.processors.add_log_level,
                         structlog.processors.StackInfoRenderer(),
                         structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S",
                                                          utc=True),

                         ]

    if is_dev:
        processors = shared_processors + [structlog.dev.set_exc_info,
                                          structlog.dev.ConsoleRenderer()]
    else:
        processors = shared_processors + [structlog.processors.dict_tracebacks,
                                          structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )
