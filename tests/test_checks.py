import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError


def test_storage_check():
    call_command("check")

    with pytest.raises(SystemCheckError) as e:
        call_command("check", "--deploy")

    assert ("FileSystemStorage should not be used in a production environment.") in str(
        e.value
    )
