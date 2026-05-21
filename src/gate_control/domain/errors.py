class GateControlError(Exception):
    """Base error for gate control operations."""


class ProtocolError(GateControlError):
    """Raised when a TCP frame cannot be parsed or validated."""


class ConnectionNotConfiguredError(GateControlError):
    """Raised when no default controller is configured."""


class GateConnectionError(GateControlError):
    """Raised when TCP connection fails."""


class CommandTimeoutError(GateControlError):
    """Raised when a controller command does not receive a response in time."""


class UnsafeCommandError(GateControlError):
    """Raised when a destructive command is requested without confirmation."""


class MissingHeartbeatError(GateControlError):
    """Raised when a command needs heartbeat-derived state but none is available."""
