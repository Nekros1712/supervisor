"""Init file for Supervisor info RESTful API."""
import logging
from typing import Any

from aiohttp import web

from ..const import (
    ATTR_ARCH,
    ATTR_CHANNEL,
    ATTR_DOCKER,
    ATTR_FEATURES,
    ATTR_HASSOS,
    ATTR_HOMEASSISTANT,
    ATTR_HOSTNAME,
    ATTR_LOGGING,
    ATTR_MACHINE,
    ATTR_OPERATING_SYSTEM,
    ATTR_STATE,
    ATTR_SUPERVISOR,
    ATTR_SUPPORTED,
    ATTR_SUPPORTED_ARCH,
    ATTR_TIMEZONE,
)
from ..coresys import CoreSysAttributes
from .utils import api_process

_LOGGER: logging.Logger = logging.getLogger(__name__)


class APIInfo(CoreSysAttributes):
    """Handle RESTful API for info functions."""

    @api_process
    async def info(self, request: web.Request) -> dict[str, Any]:
        """Show system info."""
        return {
            ATTR_SUPERVISOR: self.sys_supervisor.version,
            ATTR_HOMEASSISTANT: self.sys_homeassistant.version,
            ATTR_HASSOS: self.sys_os.version,
            ATTR_DOCKER: self.sys_docker.info.version,
            ATTR_HOSTNAME: self.sys_host.info.hostname,
            ATTR_OPERATING_SYSTEM: self.sys_host.info.operating_system,
            ATTR_FEATURES: self.sys_host.features,
            ATTR_MACHINE: self.sys_machine,
            ATTR_ARCH: self.sys_arch.default,
            ATTR_STATE: self.sys_core.state,
            ATTR_SUPPORTED_ARCH: self.sys_arch.supported,
            ATTR_SUPPORTED: self.sys_core.supported,
            ATTR_CHANNEL: self.sys_updater.channel,
            ATTR_LOGGING: self.sys_config.logging,
            ATTR_TIMEZONE: self.sys_timezone,
        }
