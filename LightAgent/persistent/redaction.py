"""Best-effort known-credential redaction; not a secret discovery service."""
import os


def secrets():
    return {value for key,value in os.environ.items() if len(value)>=8 and
            any(word in key.upper() for word in ('API_KEY','TOKEN','PASSWORD','SECRET'))}


def contains_secret(data):
    if isinstance(data, bytes):
        return any(value.encode() in data for value in secrets())
    return any(value in data for value in secrets())


def redact(text):
    for value in secrets():
        text=text.replace(value,'[REDACTED]')
    return text
