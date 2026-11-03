import pytest
from redpitayafpga_mcp.config import Settings

def test_safe_defaults():
    settings = Settings.from_env({})
    assert settings.project_root is None
    assert not settings.allow_project_write
    assert not settings.allow_local_build
    assert settings.vivado_executable is None

@pytest.mark.parametrize("env", [
    {"RP_PROJECT_ROOT": "relative"},
    {"RP_VIVADO_EXECUTABLE": "relative"},
    {"RP_BUILD_TIMEOUT": "nan"},
    {"RP_BUILD_TIMEOUT": "3601"},
    {"RP_ALLOW_PROJECT_WRITE": "sure"},
    {"RP_ALLOW_LOCAL_BUILD": "sure"},
])
def test_reject_invalid_settings(env):
    with pytest.raises(ValueError):
        Settings.from_env(env)
