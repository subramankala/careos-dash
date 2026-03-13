from __future__ import annotations

from app.services.careos_client import MockCareOSClient
from app.services.dashboard_service import DashboardService
from app.services.url_service import SignedURLService

careos_client = MockCareOSClient()
dashboard_service = DashboardService(careos_client)
url_service = SignedURLService()
