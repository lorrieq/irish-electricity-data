class IrishElectricityDataError(Exception):
    """Base class for all errors raised by this library."""


class ProviderError(IrishElectricityDataError):
    """Upstream provider returned an error response or malformed data."""


class ProviderTimeout(ProviderError):
    """Upstream provider did not respond within the configured retry budget."""


class ProviderRateLimited(ProviderError):
    """Upstream provider signalled rate limiting (HTTP 429 or WAF)."""


class ReportNotFoundError(ProviderError):
    """A report reference could not be located on the upstream provider."""


class ParseError(IrishElectricityDataError):
    """A payload could not be parsed into the expected schema."""


class TimezoneAmbiguityError(IrishElectricityDataError):
    """A datetime fell inside a DST transition that could not be resolved."""
