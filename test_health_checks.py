"""
Comprehensive tests for health checks
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from health_checks import (
    HealthStatus, HealthCheckResult, BaseHealthCheck,
    SystemResourcesHealthCheck, DatabaseHealthCheck,
    ExternalServiceHealthCheck, ApplicationHealthCheck,
    HealthCheckManager, setup_default_health_checks
)

class TestHealthStatus:
    """Test cases for HealthStatus enum"""
    
    def test_health_status_values(self):
        """Test health status enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

class TestHealthCheckResult:
    """Test cases for HealthCheckResult dataclass"""
    
    def test_health_check_result_creation(self):
        """Test health check result creation"""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All good",
            details={"metric": "value"},
            duration=0.1
        )
        
        assert result.name == "test_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.details == {"metric": "value"}
        assert result.duration == 0.1
        assert isinstance(result.timestamp, float)
    
    def test_health_check_result_defaults(self):
        """Test health check result with defaults"""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY
        )
        
        assert result.message == ""
        assert result.details == {}
        assert result.duration == 0.0

class TestBaseHealthCheck:
    """Test cases for BaseHealthCheck"""
    
    def test_base_health_check_creation(self):
        """Test base health check creation"""
        check = BaseHealthCheck("test_check", timeout=5.0)
        assert check.name == "test_check"
        assert check.timeout == 5.0
        assert check.enabled is True
    
    def test_base_health_check_defaults(self):
        """Test base health check with defaults"""
        check = BaseHealthCheck("test_check")
        assert check.timeout == 10.0
        assert check.enabled is True
    
    @pytest.mark.asyncio
    async def test_base_health_check_execute_not_implemented(self):
        """Test base health check execute method not implemented"""
        check = BaseHealthCheck("test_check")
        
        with pytest.raises(NotImplementedError):
            await check.execute()
    
    @pytest.mark.asyncio
    async def test_base_health_check_run_disabled(self):
        """Test running disabled health check"""
        check = BaseHealthCheck("test_check")
        check.enabled = False
        
        result = await check.run()
        assert result.name == "test_check"
        assert result.status == HealthStatus.UNKNOWN
        assert "disabled" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_base_health_check_run_timeout(self):
        """Test health check timeout"""
        class SlowHealthCheck(BaseHealthCheck):
            async def execute(self):
                await asyncio.sleep(0.2)  # Longer than timeout
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY
                )
        
        check = SlowHealthCheck("slow_check", timeout=0.1)
        result = await check.run()
        
        assert result.name == "slow_check"
        assert result.status == HealthStatus.UNHEALTHY
        assert "timeout" in result.message.lower()

class TestSystemResourcesHealthCheck:
    """Test cases for SystemResourcesHealthCheck"""
    
    @patch('health_checks.psutil')
    @pytest.mark.asyncio
    async def test_system_resources_healthy(self, mock_psutil):
        """Test system resources check when healthy"""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        mock_psutil.disk_usage.return_value = Mock(percent=70.0)
        
        check = SystemResourcesHealthCheck(
            cpu_threshold=80.0,
            memory_threshold=80.0,
            disk_threshold=80.0
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.details['cpu_percent'] == 50.0
        assert result.details['memory_percent'] == 60.0
        assert result.details['disk_percent'] == 70.0
    
    @patch('health_checks.psutil')
    @pytest.mark.asyncio
    async def test_system_resources_degraded(self, mock_psutil):
        """Test system resources check when degraded"""
        # Mock high resource usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
        mock_psutil.disk_usage.return_value = Mock(percent=70.0)
        
        check = SystemResourcesHealthCheck(
            cpu_threshold=80.0,
            memory_threshold=80.0,
            disk_threshold=80.0
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.DEGRADED
        assert "CPU usage high" in result.message
    
    @patch('health_checks.psutil')
    @pytest.mark.asyncio
    async def test_system_resources_unhealthy(self, mock_psutil):
        """Test system resources check when unhealthy"""
        # Mock very high resource usage
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.virtual_memory.return_value = Mock(percent=95.0)
        mock_psutil.disk_usage.return_value = Mock(percent=95.0)
        
        check = SystemResourcesHealthCheck(
            cpu_threshold=80.0,
            memory_threshold=80.0,
            disk_threshold=80.0
        )
        
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "CPU usage critical" in result.message
        assert "Memory usage critical" in result.message
        assert "Disk usage critical" in result.message
    
    @patch('health_checks.psutil')
    @pytest.mark.asyncio
    async def test_system_resources_error(self, mock_psutil):
        """Test system resources check with error"""
        # Mock psutil error
        mock_psutil.cpu_percent.side_effect = Exception("psutil error")
        
        check = SystemResourcesHealthCheck()
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "error" in result.message.lower()

class TestDatabaseHealthCheck:
    """Test cases for DatabaseHealthCheck"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.faiss"
        self.test_file.touch()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_database_healthy(self):
        """Test database check when healthy"""
        check = DatabaseHealthCheck([str(self.test_file)])
        result = await check.execute()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.details['files_checked'] == 1
        assert result.details['files_found'] == 1
    
    @pytest.mark.asyncio
    async def test_database_missing_files(self):
        """Test database check with missing files"""
        missing_file = Path(self.temp_dir) / "missing.faiss"
        check = DatabaseHealthCheck([str(self.test_file), str(missing_file)])
        result = await check.execute()
        
        assert result.status == HealthStatus.DEGRADED
        assert result.details['files_checked'] == 2
        assert result.details['files_found'] == 1
        assert "missing" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_database_no_files(self):
        """Test database check with no files"""
        check = DatabaseHealthCheck([])
        result = await check.execute()
        
        assert result.status == HealthStatus.UNKNOWN
        assert "no files" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_database_all_missing(self):
        """Test database check with all files missing"""
        missing_file1 = Path(self.temp_dir) / "missing1.faiss"
        missing_file2 = Path(self.temp_dir) / "missing2.faiss"
        check = DatabaseHealthCheck([str(missing_file1), str(missing_file2)])
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert result.details['files_found'] == 0

class TestExternalServiceHealthCheck:
    """Test cases for ExternalServiceHealthCheck"""
    
    @patch('health_checks.aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_external_service_healthy(self, mock_session_class):
        """Test external service check when healthy"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        check = ExternalServiceHealthCheck("http://example.com/health")
        result = await check.execute()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.details['status_code'] == 200
        assert result.details['response_time'] > 0
    
    @patch('health_checks.aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_external_service_unhealthy_status(self, mock_session_class):
        """Test external service check with unhealthy status code"""
        # Mock error response
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        check = ExternalServiceHealthCheck("http://example.com/health")
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert result.details['status_code'] == 500
    
    @patch('health_checks.aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_external_service_connection_error(self, mock_session_class):
        """Test external service check with connection error"""
        # Mock connection error
        mock_session = Mock()
        mock_session.get = AsyncMock(side_effect=Exception("Connection failed"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        check = ExternalServiceHealthCheck("http://example.com/health")
        result = await check.execute()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "connection failed" in result.message.lower()

class TestApplicationHealthCheck:
    """Test cases for ApplicationHealthCheck"""
    
    @pytest.mark.asyncio
    async def test_application_healthy(self):
        """Test application check when healthy"""
        mock_app = Mock()
        mock_app.start_time = time.time() - 3600  # 1 hour ago
        
        check = ApplicationHealthCheck(mock_app)
        result = await check.execute()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.details['uptime'] > 3500  # Approximately 1 hour
        assert 'start_time' in result.details
    
    @pytest.mark.asyncio
    async def test_application_no_start_time(self):
        """Test application check without start time"""
        mock_app = Mock()
        del mock_app.start_time  # No start_time attribute
        
        check = ApplicationHealthCheck(mock_app)
        result = await check.execute()
        
        assert result.status == HealthStatus.UNKNOWN
        assert "no start time" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_application_recently_started(self):
        """Test application check for recently started app"""
        mock_app = Mock()
        mock_app.start_time = time.time() - 10  # 10 seconds ago
        
        check = ApplicationHealthCheck(mock_app, min_uptime=60)
        result = await check.execute()
        
        assert result.status == HealthStatus.DEGRADED
        assert "recently started" in result.message.lower()

class TestHealthCheckManager:
    """Test cases for HealthCheckManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = HealthCheckManager()
    
    def test_add_health_check(self):
        """Test adding health check"""
        check = BaseHealthCheck("test_check")
        self.manager.add_check(check)
        
        assert "test_check" in self.manager.checks
        assert self.manager.checks["test_check"] == check
    
    def test_remove_health_check(self):
        """Test removing health check"""
        check = BaseHealthCheck("test_check")
        self.manager.add_check(check)
        
        removed = self.manager.remove_check("test_check")
        assert removed == check
        assert "test_check" not in self.manager.checks
    
    def test_remove_nonexistent_check(self):
        """Test removing non-existent health check"""
        removed = self.manager.remove_check("nonexistent")
        assert removed is None
    
    def test_get_health_check(self):
        """Test getting health check"""
        check = BaseHealthCheck("test_check")
        self.manager.add_check(check)
        
        retrieved = self.manager.get_check("test_check")
        assert retrieved == check
    
    def test_get_nonexistent_check(self):
        """Test getting non-existent health check"""
        retrieved = self.manager.get_check("nonexistent")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_run_all_checks_empty(self):
        """Test running all checks when no checks exist"""
        results = await self.manager.run_all_checks()
        assert results == {}
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all health checks"""
        # Create mock checks
        class MockHealthCheck(BaseHealthCheck):
            def __init__(self, name, status):
                super().__init__(name)
                self.status = status
            
            async def execute(self):
                return HealthCheckResult(
                    name=self.name,
                    status=self.status
                )
        
        check1 = MockHealthCheck("check1", HealthStatus.HEALTHY)
        check2 = MockHealthCheck("check2", HealthStatus.DEGRADED)
        
        self.manager.add_check(check1)
        self.manager.add_check(check2)
        
        results = await self.manager.run_all_checks()
        
        assert len(results) == 2
        assert results["check1"].status == HealthStatus.HEALTHY
        assert results["check2"].status == HealthStatus.DEGRADED
    
    @pytest.mark.asyncio
    async def test_get_overall_status_healthy(self):
        """Test overall status when all checks are healthy"""
        class MockHealthCheck(BaseHealthCheck):
            async def execute(self):
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY
                )
        
        self.manager.add_check(MockHealthCheck("check1"))
        self.manager.add_check(MockHealthCheck("check2"))
        
        status = await self.manager.get_overall_status()
        assert status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_get_overall_status_degraded(self):
        """Test overall status when some checks are degraded"""
        class MockHealthCheck(BaseHealthCheck):
            def __init__(self, name, status):
                super().__init__(name)
                self.status = status
            
            async def execute(self):
                return HealthCheckResult(
                    name=self.name,
                    status=self.status
                )
        
        self.manager.add_check(MockHealthCheck("check1", HealthStatus.HEALTHY))
        self.manager.add_check(MockHealthCheck("check2", HealthStatus.DEGRADED))
        
        status = await self.manager.get_overall_status()
        assert status == HealthStatus.DEGRADED
    
    @pytest.mark.asyncio
    async def test_get_overall_status_unhealthy(self):
        """Test overall status when any check is unhealthy"""
        class MockHealthCheck(BaseHealthCheck):
            def __init__(self, name, status):
                super().__init__(name)
                self.status = status
            
            async def execute(self):
                return HealthCheckResult(
                    name=self.name,
                    status=self.status
                )
        
        self.manager.add_check(MockHealthCheck("check1", HealthStatus.HEALTHY))
        self.manager.add_check(MockHealthCheck("check2", HealthStatus.UNHEALTHY))
        
        status = await self.manager.get_overall_status()
        assert status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_summary(self):
        """Test getting health check summary"""
        class MockHealthCheck(BaseHealthCheck):
            def __init__(self, name, status):
                super().__init__(name)
                self.status = status
            
            async def execute(self):
                return HealthCheckResult(
                    name=self.name,
                    status=self.status,
                    duration=0.1
                )
        
        self.manager.add_check(MockHealthCheck("check1", HealthStatus.HEALTHY))
        self.manager.add_check(MockHealthCheck("check2", HealthStatus.DEGRADED))
        self.manager.add_check(MockHealthCheck("check3", HealthStatus.UNHEALTHY))
        
        summary = await self.manager.get_summary()
        
        assert summary['overall_status'] == HealthStatus.UNHEALTHY
        assert summary['total_checks'] == 3
        assert summary['healthy_checks'] == 1
        assert summary['degraded_checks'] == 1
        assert summary['unhealthy_checks'] == 1
        assert summary['total_duration'] > 0

class TestSetupDefaultHealthChecks:
    """Test cases for setup_default_health_checks function"""
    
    def test_setup_default_health_checks(self):
        """Test setting up default health checks"""
        mock_app = Mock()
        mock_app.start_time = time.time()
        
        manager = setup_default_health_checks(mock_app)
        
        assert isinstance(manager, HealthCheckManager)
        assert len(manager.checks) > 0
        
        # Check that expected checks are present
        check_names = list(manager.checks.keys())
        assert "system_resources" in check_names
        assert "application" in check_names
    
    def test_setup_with_database_files(self):
        """Test setup with database files"""
        mock_app = Mock()
        mock_app.start_time = time.time()
        
        manager = setup_default_health_checks(
            mock_app,
            database_files=["test1.faiss", "test2.faiss"]
        )
        
        assert "database" in manager.checks
        db_check = manager.get_check("database")
        assert isinstance(db_check, DatabaseHealthCheck)
    
    def test_setup_with_external_services(self):
        """Test setup with external services"""
        mock_app = Mock()
        mock_app.start_time = time.time()
        
        external_services = [
            "http://service1.com/health",
            "http://service2.com/health"
        ]
        
        manager = setup_default_health_checks(
            mock_app,
            external_services=external_services
        )
        
        # Should have external service checks
        service_checks = [name for name in manager.checks.keys() 
                         if name.startswith("external_service_")]
        assert len(service_checks) == 2

class TestIntegration:
    """Integration tests for health check system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_health_check_pipeline(self):
        """Test complete health check pipeline"""
        # Create test files
        test_file = Path(self.temp_dir) / "test.faiss"
        test_file.touch()
        
        # Create mock app
        mock_app = Mock()
        mock_app.start_time = time.time() - 100  # Started 100 seconds ago
        
        # Setup health checks
        manager = setup_default_health_checks(
            mock_app,
            database_files=[str(test_file)]
        )
        
        # Run all checks
        results = await manager.run_all_checks()
        
        # Verify results
        assert len(results) > 0
        assert all(isinstance(result, HealthCheckResult) for result in results.values())
        
        # Get summary
        summary = await manager.get_summary()
        assert 'overall_status' in summary
        assert 'total_checks' in summary
        assert summary['total_checks'] == len(results)
    
    @patch('health_checks.psutil')
    @pytest.mark.asyncio
    async def test_health_check_with_resource_constraints(self, mock_psutil):
        """Test health checks under resource constraints"""
        # Mock high resource usage
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.virtual_memory.return_value = Mock(percent=90.0)
        mock_psutil.disk_usage.return_value = Mock(percent=85.0)
        
        manager = HealthCheckManager()
        manager.add_check(SystemResourcesHealthCheck(
            cpu_threshold=80.0,
            memory_threshold=80.0,
            disk_threshold=80.0
        ))
        
        results = await manager.run_all_checks()
        overall_status = await manager.get_overall_status()
        
        assert overall_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert results["system_resources"].status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

if __name__ == '__main__':
    pytest.main([__file__])