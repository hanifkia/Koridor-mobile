from datetime import datetime
from enum import Enum
import json
from typing import Any
import logging

import httpx
from typing_extensions import Self

from .schemas.geospatial import (
    TrendRouteGeoSpatialDirectionsRequest,
    TrendRouteGeoSpatialDirectionsResponse,
)
from .schemas import (
    TrendRouteOptimizationRequestModel,
    TrendRouteOptimizationResponseModel,
    TrendRouteRecalculationRequestModel,
    TrendRouteRecalculationResponseModel,
)

from app.config.settings import settings


class TrendRouteAsyncClient:
    """Async client responsible for communicating with the Trend Route engine."""

    class TrendRouteEndpoints(Enum):
        SOLVE_ROUTE_OPTIMIZATION = settings.TRENDROUTE_SOLVE_ROUTE_OPTIMIZATION_ENDPOINT
        SOLVE_ROUTE_RECALCULATION = (
            settings.TRENDROUTE_SOLVE_ROUTE_RECALCULATION_ENDPOINT
        )
        GEOSPATIAL_DIRECTIONS = settings.TRENDROUTE_GEOSPATIAL_DIRECTIONS_ENDPOINT

    def __init__(self) -> None:
        self.__service_url = settings.TRENDROUTE_SERVICE_URL
        self.__client: httpx.AsyncClient | None = None
        self.__endpoints = self.__class__.TrendRouteEndpoints
        self._logger = logging.getLogger(__name__)

    async def __aenter__(self) -> Self:
        self.__client = httpx.AsyncClient(
            base_url=self.__service_url,
            timeout=None,
            headers={"X-API-Key": settings.TRENDROUTE_API_KEY},
        )
        self._logger.info(f"🔌 TrendRoute client connected to {self.__service_url}")
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.__client is not None:
            await self.__client.aclose()
            self.__client = None
            self._logger.info("🔌 TrendRoute client disconnected")

    def __ensure_in_context(self) -> None:
        if self.__client is None:
            raise RuntimeError(
                "TrendRouteAsyncClient must be used within an async context manager."
            )

    async def solve_and_get_solution(
        self, solve_request_data: TrendRouteOptimizationRequestModel
    ) -> TrendRouteOptimizationResponseModel:
        """Submit the optimization request payload and parse the Trend Route solution."""

        self.__ensure_in_context()
        endpoint = self.__endpoints.SOLVE_ROUTE_OPTIMIZATION.value

        self._logger.debug(f"📤 Sending optimization request to {endpoint}")

        try:
            response = await self.__client.post(
                endpoint, json=solve_request_data.model_dump()
            )
            response.raise_for_status()

            self._logger.debug(
                f"📥 Received response with status {response.status_code}"
            )

            result = TrendRouteOptimizationResponseModel.model_validate(response.json())
            self._logger.info(
                f"✅ Optimization successful: {len(result.routes)} routes, "
                f"{len(result.unassigned_order_ids)} unassigned orders"
            )
            return result

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"❌ TrendRoute API returned error {e.response.status_code}: {e.response.text}",
                exc_info=True,
            )
            raise
        except Exception as e:
            self._logger.error(
                f"❌ Failed to get solution from TrendRoute: {str(e)}", exc_info=True
            )
            raise

    async def recalculate_route(
        self, recalc_request_data: TrendRouteRecalculationRequestModel
    ) -> TrendRouteRecalculationResponseModel:
        """Submit a recalculation payload and parse the Trend Route recalculated route."""

        self.__ensure_in_context()
        endpoint = self.__endpoints.SOLVE_ROUTE_RECALCULATION.value

        payload = recalc_request_data.model_dump(exclude_none=True)

        self._logger.debug(f"📤 Sending recalculation request to {endpoint}")

        try:
            response = await self.__client.post(endpoint, json=payload)
            response.raise_for_status()

            self._logger.debug(
                f"📥 Received recalculation response with status {response.status_code}"
            )

            result = TrendRouteRecalculationResponseModel.model_validate(
                response.json()
            )
            self._logger.info("✅ Route recalculation successful")
            return result

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"❌ TrendRoute recalculation API returned error {e.response.status_code}: {e.response.text}",
                exc_info=True,
            )
            raise
        except Exception as e:
            self._logger.error(
                f"❌ Failed to recalculate route: {str(e)}", exc_info=True
            )
            raise

    async def get_routes_directions(
        self, geospatial_request_data: TrendRouteGeoSpatialDirectionsRequest
    ) -> TrendRouteGeoSpatialDirectionsResponse:
        """Get geospatial directions for routes."""

        self.__ensure_in_context()
        endpoint = self.__endpoints.GEOSPATIAL_DIRECTIONS.value

        payload = geospatial_request_data.model_dump(exclude_none=True)

        self._logger.debug(f"📤 Sending geospatial directions request to {endpoint}")

        try:
            response = await self.__client.post(endpoint, json=payload)
            response.raise_for_status()

            self._logger.debug(
                f"📥 Received geospatial response with status {response.status_code}"
            )

            result = TrendRouteGeoSpatialDirectionsResponse.model_validate(
                response.json()
            )
            self._logger.info(
                f"✅ Geospatial directions retrieved: {result.distance}m, {result.duration}s"
            )
            return result

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"❌ TrendRoute geospatial API returned error {e.response.status_code}: {e.response.text}",
                exc_info=True,
            )
            raise
        except Exception as e:
            self._logger.error(
                f"❌ Failed to get geospatial directions: {str(e)}", exc_info=True
            )
            raise
