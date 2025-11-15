"""
Load Testing - 100 Concurrent Users Simulation

Tests system performance under realistic load:
- Simulates 100 concurrent users
- Tests critical endpoints
- Measures response times and throughput
"""
import asyncio
import time
from typing import List, Dict, Tuple
import statistics
from httpx import AsyncClient
import random


class LoadTestMetrics:
    """Collects and analyzes load test metrics"""

    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[Dict] = []
        self.status_codes: Dict[int, int] = {}
        self.endpoint_metrics: Dict[str, List[float]] = {}
        self.start_time = time.time()
        self.end_time = None

    def record_request(self, endpoint: str, duration: float, status_code: int, error: str = None):
        """Record a single request's metrics"""
        self.response_times.append(duration)

        if endpoint not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint] = []
        self.endpoint_metrics[endpoint].append(duration)

        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

        if error:
            self.errors.append({
                "endpoint": endpoint,
                "error": error,
                "duration": duration
            })

    def finalize(self):
        """Mark test as complete"""
        self.end_time = time.time()

    def get_report(self) -> Dict:
        """Generate comprehensive test report"""
        if not self.response_times:
            return {"error": "No requests completed"}

        total_time = self.end_time - self.start_time
        total_requests = len(self.response_times)

        report = {
            "summary": {
                "total_time_seconds": round(total_time, 2),
                "total_requests": total_requests,
                "successful_requests": sum(1 for code in self.status_codes if 200 <= code < 400),
                "failed_requests": len(self.errors),
                "requests_per_second": round(total_requests / total_time, 2)
            },
            "response_times": {
                "average_ms": round(statistics.mean(self.response_times) * 1000, 2),
                "median_ms": round(statistics.median(self.response_times) * 1000, 2),
                "min_ms": round(min(self.response_times) * 1000, 2),
                "max_ms": round(max(self.response_times) * 1000, 2),
                "p95_ms": round(statistics.quantiles(self.response_times, n=20)[18] * 1000, 2),
                "p99_ms": round(statistics.quantiles(self.response_times, n=100)[98] * 1000, 2)
            },
            "status_codes": self.status_codes,
            "endpoint_analysis": {}
        }

        # Analyze each endpoint
        for endpoint, times in self.endpoint_metrics.items():
            avg_time = statistics.mean(times)
            max_time = max(times)

            analysis = {
                "requests": len(times),
                "avg_ms": round(avg_time * 1000, 2),
                "max_ms": round(max_time * 1000, 2)
            }

            # Performance warnings
            if max_time > 10:
                analysis["warning"] = f"SLOW: Max response time {max_time:.1f}s"
            elif avg_time > 5:
                analysis["warning"] = f"SLOW AVG: Average response time {avg_time:.1f}s"

            report["endpoint_analysis"][endpoint] = analysis

        return report


class VirtualUser:
    """Simulates a single user's behavior"""

    def __init__(self, user_id: int, metrics: LoadTestMetrics):
        self.user_id = user_id
        self.metrics = metrics
        self.email = f"loadtest_{user_id}@example.com"
        self.token = None

    async def run_user_journey(self, client: AsyncClient):
        """Execute a realistic user journey"""

        # Journey: Signup → Login → Dashboard → Upload Draft → Analytics

        # 1. Signup (30% of users)
        if random.random() < 0.3:
            await self._signup(client)

        # 2. Login (all users)
        login_success = await self._login(client)

        if not login_success:
            return  # Stop if login fails

        # 3. Dashboard access (100% of users)
        await self._access_dashboard(client)

        # 4. Create draft (50% of users)
        if random.random() < 0.5:
            await self._create_draft(client)

        # 5. AI operations (30% of users)
        if random.random() < 0.3:
            await self._ai_operations(client)

        # 6. Analytics (20% of users)
        if random.random() < 0.2:
            await self._view_analytics(client)

    async def _signup(self, client: AsyncClient):
        """Simulate user signup"""
        start = time.time()
        try:
            response = await client.post("/api/auth/register", json={
                "email": self.email,
                "password": "TestPass123!",
                "name": f"Load Test User {self.user_id}"
            }, timeout=30.0)

            duration = time.time() - start
            self.metrics.record_request("POST /api/auth/register", duration, response.status_code)

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("POST /api/auth/register", duration, 0, str(e))

    async def _login(self, client: AsyncClient) -> bool:
        """Simulate user login"""
        start = time.time()
        try:
            response = await client.post("/api/auth/login", json={
                "email": self.email,
                "password": "TestPass123!"
            }, timeout=30.0)

            duration = time.time() - start
            self.metrics.record_request("POST /api/auth/login", duration, response.status_code)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token') or data.get('token')
                return True

            return False

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("POST /api/auth/login", duration, 0, str(e))
            return False

    async def _access_dashboard(self, client: AsyncClient):
        """Simulate dashboard access"""
        if not self.token:
            return

        start = time.time()
        try:
            response = await client.get(
                "/api/v1/dashboard/stats",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0
            )

            duration = time.time() - start
            self.metrics.record_request("GET /api/v1/dashboard/stats", duration, response.status_code)

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("GET /api/v1/dashboard/stats", duration, 0, str(e))

    async def _create_draft(self, client: AsyncClient):
        """Simulate draft creation"""
        if not self.token:
            return

        start = time.time()
        try:
            response = await client.post(
                "/api/v1/drafts/create-from-photos",
                json={
                    "photo_urls": ["/test/photo1.jpg"],
                    "style": random.choice(["casual_friendly", "professional", "trendy"]),
                    "language": random.choice(["fr", "en"])
                },
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=60.0  # AI operations can be slower
            )

            duration = time.time() - start
            self.metrics.record_request("POST /api/v1/drafts/create-from-photos", duration, response.status_code)

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("POST /api/v1/drafts/create-from-photos", duration, 0, str(e))

    async def _ai_operations(self, client: AsyncClient):
        """Simulate AI message generation"""
        if not self.token:
            return

        start = time.time()
        try:
            response = await client.post(
                "/api/v1/ai-messages/generate-response",
                json={
                    "message": "Is this item still available?",
                    "article_context": {
                        "title": "Test Item",
                        "price": 25.0
                    },
                    "tone": "friendly"
                },
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=60.0
            )

            duration = time.time() - start
            self.metrics.record_request("POST /api/v1/ai-messages/generate-response", duration, response.status_code)

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("POST /api/v1/ai-messages/generate-response", duration, 0, str(e))

    async def _view_analytics(self, client: AsyncClient):
        """Simulate analytics access"""
        if not self.token:
            return

        start = time.time()
        try:
            response = await client.get(
                "/api/v1/analytics-ml/kpis",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0
            )

            duration = time.time() - start
            self.metrics.record_request("GET /api/v1/analytics-ml/kpis", duration, response.status_code)

        except Exception as e:
            duration = time.time() - start
            self.metrics.record_request("GET /api/v1/analytics-ml/kpis", duration, 0, str(e))


async def run_load_test(num_users: int = 100, base_url: str = "http://localhost:5000"):
    """
    Run load test with specified number of concurrent users

    Args:
        num_users: Number of concurrent users to simulate
        base_url: API base URL
    """

    print("\n" + "="*70)
    print(f"🔥 LOAD TEST - {num_users} CONCURRENT USERS")
    print("="*70)

    metrics = LoadTestMetrics()

    async with AsyncClient(base_url=base_url) as client:
        # Create virtual users
        users = [VirtualUser(i, metrics) for i in range(num_users)]

        print(f"\n🚀 Starting {num_users} concurrent user sessions...")
        start_time = time.time()

        # Run all users concurrently
        tasks = [user.run_user_journey(client) for user in users]
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics.finalize()

        # Generate report
        print(f"\n✅ Test completed in {time.time() - start_time:.2f}s")
        print("\n" + "="*70)
        print("📊 LOAD TEST RESULTS")
        print("="*70)

        report = metrics.get_report()

        # Summary
        summary = report["summary"]
        print(f"\n📈 SUMMARY:")
        print(f"  Total time: {summary['total_time_seconds']}s")
        print(f"  Total requests: {summary['total_requests']}")
        print(f"  Successful: {summary['successful_requests']}")
        print(f"  Failed: {summary['failed_requests']}")
        print(f"  Throughput: {summary['requests_per_second']} req/s")

        # Response times
        times = report["response_times"]
        print(f"\n⏱️  RESPONSE TIMES:")
        print(f"  Average: {times['average_ms']}ms")
        print(f"  Median: {times['median_ms']}ms")
        print(f"  Min: {times['min_ms']}ms")
        print(f"  Max: {times['max_ms']}ms")
        print(f"  P95: {times['p95_ms']}ms")
        print(f"  P99: {times['p99_ms']}ms")

        # Status codes
        print(f"\n📊 STATUS CODES:")
        for code, count in sorted(report["status_codes"].items()):
            print(f"  {code}: {count} requests")

        # Endpoint analysis
        print(f"\n🎯 ENDPOINT PERFORMANCE:")
        for endpoint, analysis in report["endpoint_analysis"].items():
            warning = analysis.get("warning", "")
            status_icon = "⚠️" if warning else "✅"
            print(f"  {status_icon} {endpoint}")
            print(f"     {analysis['requests']} requests | Avg: {analysis['avg_ms']}ms | Max: {analysis['max_ms']}ms")
            if warning:
                print(f"     🔴 {warning}")

        # Errors
        if metrics.errors:
            print(f"\n🔴 ERRORS ({len(metrics.errors)}):")
            error_summary = {}
            for error in metrics.errors[:10]:  # Show first 10
                endpoint = error['endpoint']
                error_summary[endpoint] = error_summary.get(endpoint, 0) + 1

            for endpoint, count in error_summary.items():
                print(f"  • {endpoint}: {count} errors")

        print("\n" + "="*70)

        # Performance warnings
        slow_endpoints = [
            endpoint for endpoint, analysis in report["endpoint_analysis"].items()
            if "warning" in analysis
        ]

        if slow_endpoints:
            print("\n⚠️  PERFORMANCE WARNINGS:")
            print("The following endpoints are slow and need optimization:")
            for endpoint in slow_endpoints:
                analysis = report["endpoint_analysis"][endpoint]
                print(f"  • {endpoint}: {analysis['warning']}")
        else:
            print("\n🎉 ALL ENDPOINTS PERFORMING WELL!")

        return report


if __name__ == "__main__":
    # Run load test
    asyncio.run(run_load_test(num_users=100))
