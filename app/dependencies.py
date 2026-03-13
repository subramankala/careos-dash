from __future__ import annotations

from app.services.authorization_service import AuthorizationService
from app.services.careos_client import CareOSMCPClient
from app.services.dashboard_service import DashboardService
from app.services.openclaw_ingress_service import OpenClawIngressService
from app.services.url_service import SignedURLService

careos_client = CareOSMCPClient()
authorization_service = AuthorizationService(careos_client)
dashboard_service = DashboardService(careos_client)
url_service = SignedURLService()
openclaw_ingress_service = OpenClawIngressService(authorization_service, url_service)
