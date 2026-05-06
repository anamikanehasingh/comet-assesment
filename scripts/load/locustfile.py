"""Locust skeleton for ride + location traffic (extend with JWT acquisition)."""

from locust import HttpUser, between, task


class RiderDriverUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def health(self) -> None:
        self.client.get("/health")

    @task(1)
    def pricing_estimate(self) -> None:
        self.client.get(
            "/api/v1/pricing/estimate",
            params={
                "pickup_lat": 40.73,
                "pickup_lng": -73.99,
                "dest_lat": 40.78,
                "dest_lng": -73.96,
            },
        )
