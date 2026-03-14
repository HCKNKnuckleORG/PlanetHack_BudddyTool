"""
PlanetHack Modules
Each module corresponds to a chapter in Bug Bounty Bootcamp
"""

from .base import BaseModule
from .recon import ReconModule
from .sql import SQLModule
from .xss import XSSModule
from .auth import AuthModule
from .file_upload import FileUploadModule
from .ssrf import SSRFModule
from .xxe import XXEModule
from .deserialization import DeserializationModule
from .api import APIModule
from .business_logic import BusinessLogicModule
from .access_control import AccessControlModule
from .session import SessionModule
from .csrf import CSRFModule
from .request_smuggling import RequestSmugglingModule
from .cache import CacheModule
from .open_redirect import OpenRedirectModule
from .clickjacking import ClickjackingModule
from .template_injection import TemplateInjectionModule
from .rce import RCEModule
from .information_disclosure import InformationDisclosureModule
from .fuzzing import FuzzingModule
from .brute_force import BruteForceModule
from .a01_broken_access_control import A01BrokenAccessControlModule
from .a02_security_misconfiguration import A02SecurityMisconfigurationModule
from .a03_supply_chain import A03SupplyChainModule
from .a04_cryptographic_failures import A04CryptographicFailuresModule
from .a05_injection import A05InjectionModule
from .a06_insecure_design import A06InsecureDesignModule
from .a07_authentication_failures import A07AuthenticationFailuresModule
from .a08_data_integrity_failures import A08DataIntegrityFailuresModule
from .a09_logging_failures import A09LoggingFailuresModule
from .a10_exceptional_conditions import A10ExceptionalConditionsModule

# Map module_id -> class for dynamic loading
MODULE_REGISTRY = {
    "recon": ReconModule,
    "sql": SQLModule,
    "xss": XSSModule,
    "auth": AuthModule,
    "file_upload": FileUploadModule,
    "ssrf": SSRFModule,
    "xxe": XXEModule,
    "deserialization": DeserializationModule,
    "api": APIModule,
    "business_logic": BusinessLogicModule,
    "access_control": AccessControlModule,
    "session": SessionModule,
    "csrf": CSRFModule,
    "request_smuggling": RequestSmugglingModule,
    "cache": CacheModule,
    "open_redirect": OpenRedirectModule,
    "clickjacking": ClickjackingModule,
    "template_injection": TemplateInjectionModule,
    "rce": RCEModule,
    "information_disclosure": InformationDisclosureModule,
    "fuzzing": FuzzingModule,
    "brute_force": BruteForceModule,
    # OWASP Top 10 2025
    "a01_access_control": A01BrokenAccessControlModule,
    "a02_misconfiguration": A02SecurityMisconfigurationModule,
    "a03_supply_chain": A03SupplyChainModule,
    "a04_crypto": A04CryptographicFailuresModule,
    "a05_injection": A05InjectionModule,
    "a06_insecure_design": A06InsecureDesignModule,
    "a07_auth": A07AuthenticationFailuresModule,
    "a08_integrity": A08DataIntegrityFailuresModule,
    "a09_logging": A09LoggingFailuresModule,
    "a10_exceptional": A10ExceptionalConditionsModule,
}

__all__ = [
    "BaseModule",
    "ReconModule",
    "SQLModule",
    "XSSModule",
    "AuthModule",
    "FileUploadModule",
    "SSRFModule",
    "XXEModule",
    "DeserializationModule",
    "APIModule",
    "BusinessLogicModule",
    "AccessControlModule",
    "SessionModule",
    "CSRFModule",
    "RequestSmugglingModule",
    "CacheModule",
    "OpenRedirectModule",
    "ClickjackingModule",
    "TemplateInjectionModule",
    "RCEModule",
    "InformationDisclosureModule",
    "FuzzingModule",
    "BruteForceModule",
    "A01BrokenAccessControlModule",
    "A02SecurityMisconfigurationModule",
    "A03SupplyChainModule",
    "A04CryptographicFailuresModule",
    "A05InjectionModule",
    "A06InsecureDesignModule",
    "A07AuthenticationFailuresModule",
    "A08DataIntegrityFailuresModule",
    "A09LoggingFailuresModule",
    "A10ExceptionalConditionsModule",
    "MODULE_REGISTRY",
]

