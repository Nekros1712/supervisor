"""AppArmor control for host."""
import logging
from pathlib import Path
import shutil

from ..coresys import CoreSysAttributes
from ..exceptions import DBusError, HostAppArmorError
from ..utils.apparmor import validate_profile

_LOGGER: logging.Logger = logging.getLogger(__name__)

SYSTEMD_SERVICES = {"hassos-apparmor.service", "hassio-apparmor.service"}


class AppArmorControl(CoreSysAttributes):
    """Handle host AppArmor controls."""

    def __init__(self, coresys):
        """Initialize host power handling."""
        self.coresys = coresys
        self._profiles = set()
        self._service = None

    @property
    def available(self):
        """Return True if AppArmor is available on host."""
        return self._service is not None

    def exists(self, profile):
        """Return True if a profile exists."""
        return profile in self._profiles

    async def _reload_service(self):
        """Reload internal service."""
        try:
            await self.sys_host.services.reload(self._service)
        except DBusError as err:
            _LOGGER.error("Can't reload %s: %s", self._service, err)

    def _get_profile(self, profile_name):
        """Get a profile from AppArmor store."""
        if profile_name not in self._profiles:
            raise HostAppArmorError(
                f"Can't find {profile_name} for removing", _LOGGER.error
            )
        return Path(self.sys_config.path_apparmor, profile_name)

    async def load(self):
        """Load available profiles."""
        for content in self.sys_config.path_apparmor.iterdir():
            if not content.is_file():
                continue
            self._profiles.add(content.name)

        # Is connected with systemd?
        _LOGGER.info("Loading AppArmor Profiles: %s", self._profiles)
        for service in SYSTEMD_SERVICES:
            if not self.sys_host.services.exists(service):
                continue
            self._service = service

        # Load profiles
        if self.available:
            await self._reload_service()
        else:
            _LOGGER.info("AppArmor is not enabled on host")

    async def load_profile(self, profile_name, profile_file):
        """Load/Update a new/exists profile into AppArmor."""
        if not validate_profile(profile_name, profile_file):
            raise HostAppArmorError(
                f"AppArmor profile '{profile_name}' is not valid", _LOGGER.error
            )

        # Copy to AppArmor folder
        dest_profile = Path(self.sys_config.path_apparmor, profile_name)
        try:
            shutil.copyfile(profile_file, dest_profile)
        except OSError as err:
            raise HostAppArmorError(
                f"Can't copy {profile_file}: {err}", _LOGGER.error
            ) from err

        # Load profiles
        _LOGGER.info("Adding/updating AppArmor profile: %s", profile_name)
        self._profiles.add(profile_name)
        if self.available:
            await self._reload_service()

    async def remove_profile(self, profile_name):
        """Remove a AppArmor profile."""
        profile_file = self._get_profile(profile_name)

        # Only remove file
        if not self.available:
            try:
                profile_file.unlink()
            except OSError as err:
                raise HostAppArmorError(
                    f"Can't remove profile: {err}", _LOGGER.error
                ) from err
            return

        # Marks als remove and start host process
        remove_profile = Path(self.sys_config.path_apparmor, "remove", profile_name)
        try:
            profile_file.rename(remove_profile)
        except OSError as err:
            raise HostAppArmorError(
                f"Can't mark profile as remove: {err}", _LOGGER.error
            ) from err

        _LOGGER.info("Removing AppArmor profile: %s", profile_name)
        self._profiles.remove(profile_name)
        await self._reload_service()

    def backup_profile(self, profile_name, backup_file):
        """Backup A profile into a new file."""
        profile_file = self._get_profile(profile_name)

        try:
            shutil.copy(profile_file, backup_file)
        except OSError as err:
            raise HostAppArmorError(
                f"Can't backup profile {profile_name}: {err}", _LOGGER.error
            ) from err
