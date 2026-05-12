"""
Performance Benchmark Command for Visitor Hostel Module
Run comprehensive performance tests and generate optimization reports
"""

import time
import statistics
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.auth.models import User

from applications.visitor_hostel.models import BookingDetail, RoomDetail
from applications.visitor_hostel.api.views import ActiveBookingsApiView
from applications.visitor_hostel.api.high_performance_views import HighPerformanceActiveBookingsApiView
from applications.visitor_hostel.selectors import (
    get_available_rooms_between_dates,
    get_confirmed_or_checkedin_bookings_for_staff
)

class Command(BaseCommand):
    help = 'Run performance benchmarks for Visitor Hostel API endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of iterations for each test (default: 10)'
        )
        parser.add_argument(
            '--endpoint',
            type=str,
            choices=['all', 'active_bookings', 'room_availability', 'dashboard'],
            default='all',
            help='Specific endpoint to benchmark'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare optimized vs original implementations'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed query information'
        )

    def handle(self, *args, **options):
        self.iterations = options['iterations']
        self.verbose = options['verbose']
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting performance benchmark with {self.iterations} iterations'
            )
        )

        # Setup test environment
        self.setup_test_data()
        
        if options['endpoint'] == 'all':
            self.run_all_benchmarks(options['compare'])
        else:
            self.run_specific_benchmark(options['endpoint'], options['compare'])

        self.cleanup_test_data()
        self.stdout.write(self.style.SUCCESS('Performance benchmark completed'))

    def setup_test_data(self):
        """Setup test data for benchmarking"""
        self.stdout.write('Setting up test data...')
        
        # Create test user if not exists
        self.test_user, created = User.objects.get_or_create(
            username='test_vhstaff',
            defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        )
        
        # Ensure we have sufficient test bookings
        existing_count = BookingDetail.objects.count()
        if existing_count < 50:
            self.stdout.write(f'Creating additional test bookings (current: {existing_count})')
            # In a real scenario, you would create test bookings here
        
        self.stdout.write(f'Test environment ready with {existing_count} bookings')

    def cleanup_test_data(self):
        """Cleanup test data"""
        # Only cleanup if test user was created for this test
        pass

    def run_all_benchmarks(self, compare_implementations=False):
        """Run benchmarks for all endpoints"""
        self.stdout.write(self.style.HTTP_INFO('\n=== RUNNING ALL BENCHMARKS ===\n'))
        
        benchmarks = [
            ('Active Bookings API', self.benchmark_active_bookings),
            ('Room Availability API', self.benchmark_room_availability),
            ('Dashboard API', self.benchmark_dashboard),
        ]

        results = {}
        for name, benchmark_func in benchmarks:
            self.stdout.write(f'\n--- {name} ---')
            results[name] = benchmark_func(compare_implementations)

        # Generate summary report
        self.generate_summary_report(results)

    def run_specific_benchmark(self, endpoint, compare_implementations=False):
        """Run benchmark for specific endpoint"""
        benchmark_map = {
            'active_bookings': self.benchmark_active_bookings,
            'room_availability': self.benchmark_room_availability,
            'dashboard': self.benchmark_dashboard,
        }
        
        if endpoint in benchmark_map:
            self.stdout.write(f'\n=== {endpoint.upper()} BENCHMARK ===\n')
            result = benchmark_map[endpoint](compare_implementations)
            self.generate_endpoint_report(endpoint, result)

    def benchmark_active_bookings(self, compare_implementations=False):
        """Benchmark active bookings endpoint"""
        self.stdout.write('Benchmarking Active Bookings endpoint...')
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get('/api/visitorhostel/bookings/active/')
        request.user = self.test_user

        # Test current implementation
        current_times = []
        current_queries = []
        
        for i in range(self.iterations):
            with self.measure_performance() as metrics:
                try:
                    view = ActiveBookingsApiView()
                    response = view.get(request)
                except Exception as e:
                    self.stdout.write(f'Error in iteration {i+1}: {str(e)}')
                    continue
            
            current_times.append(metrics['time'])
            current_queries.append(metrics['queries'])

        result = {
            'current': {
                'avg_time': statistics.mean(current_times),
                'avg_queries': statistics.mean(current_queries),
                'times': current_times,
                'queries': current_queries
            }
        }

        if compare_implementations:
            # Test optimized implementation
            optimized_times = []
            optimized_queries = []
            
            for i in range(self.iterations):
                with self.measure_performance() as metrics:
                    try:
                        view = HighPerformanceActiveBookingsApiView()
                        response = view.get(request)
                    except Exception as e:
                        self.stdout.write(f'Optimized error in iteration {i+1}: {str(e)}')
                        continue
                
                optimized_times.append(metrics['time'])
                optimized_queries.append(metrics['queries'])

            result['optimized'] = {
                'avg_time': statistics.mean(optimized_times),
                'avg_queries': statistics.mean(optimized_queries),
                'times': optimized_times,
                'queries': optimized_queries
            }

            # Calculate improvement
            time_improvement = (
                (result['current']['avg_time'] - result['optimized']['avg_time']) /
                result['current']['avg_time'] * 100
            )
            query_improvement = (
                (result['current']['avg_queries'] - result['optimized']['avg_queries']) /
                result['current']['avg_queries'] * 100
            )

            result['improvement'] = {
                'time_percent': time_improvement,
                'query_percent': query_improvement
            }

        self.print_benchmark_results('Active Bookings', result)
        return result

    def benchmark_room_availability(self, compare_implementations=False):
        """Benchmark room availability checking"""
        self.stdout.write('Benchmarking Room Availability...')
        
        from datetime import date, timedelta
        
        today = date.today()
        future_date = today + timedelta(days=7)
        
        times = []
        queries = []
        
        for i in range(self.iterations):
            with self.measure_performance() as metrics:
                try:
                    rooms = get_available_rooms_between_dates(today, future_date)
                    list(rooms)  # Force evaluation
                except Exception as e:
                    self.stdout.write(f'Error in iteration {i+1}: {str(e)}')
                    continue
            
            times.append(metrics['time'])
            queries.append(metrics['queries'])

        result = {
            'current': {
                'avg_time': statistics.mean(times),
                'avg_queries': statistics.mean(queries),
                'times': times,
                'queries': queries
            }
        }

        self.print_benchmark_results('Room Availability', result)
        return result

    def benchmark_dashboard(self, compare_implementations=False):
        """Benchmark dashboard data loading"""
        self.stdout.write('Benchmarking Dashboard data...')
        
        times = []
        queries = []
        
        for i in range(self.iterations):
            with self.measure_performance() as metrics:
                try:
                    # Simulate dashboard data loading
                    active_bookings = get_confirmed_or_checkedin_bookings_for_staff()
                    list(active_bookings[:20])  # Force evaluation with limit
                except Exception as e:
                    self.stdout.write(f'Error in iteration {i+1}: {str(e)}')
                    continue
            
            times.append(metrics['time'])
            queries.append(metrics['queries'])

        result = {
            'current': {
                'avg_time': statistics.mean(times),
                'avg_queries': statistics.mean(queries),
                'times': times,
                'queries': queries
            }
        }

        self.print_benchmark_results('Dashboard', result)
        return result

    def measure_performance(self):
        """Context manager to measure performance metrics"""
        class PerformanceMetrics:
            def __init__(self):
                self.start_time = None
                self.start_queries = None
                self.metrics = {}

            def __enter__(self):
                self.start_time = time.time()
                self.start_queries = len(connection.queries)
                return self.metrics

            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_queries = len(connection.queries)
                
                self.metrics['time'] = end_time - self.start_time
                self.metrics['queries'] = end_queries - self.start_queries

        return PerformanceMetrics()

    def print_benchmark_results(self, name, result):
        """Print formatted benchmark results"""
        self.stdout.write(f'\n{name} Results:')
        self.stdout.write('-' * 50)
        
        current = result['current']
        self.stdout.write(
            f'Current Implementation:\n'
            f'  Average Time: {current["avg_time"]:.4f}s\n'
            f'  Average Queries: {current["avg_queries"]:.1f}\n'
            f'  Min Time: {min(current["times"]):.4f}s\n'
            f'  Max Time: {max(current["times"]):.4f}s'
        )

        if 'optimized' in result:
            optimized = result['optimized']
            improvement = result['improvement']
            
            self.stdout.write(
                f'\nOptimized Implementation:\n'
                f'  Average Time: {optimized["avg_time"]:.4f}s\n'
                f'  Average Queries: {optimized["avg_queries"]:.1f}\n'
                f'  Min Time: {min(optimized["times"]):.4f}s\n'
                f'  Max Time: {max(optimized["times"]):.4f}s'
            )
            
            self.stdout.write(
                f'\nImprovement:\n'
                f'  Time: {improvement["time_percent"]:.1f}% faster\n'
                f'  Queries: {improvement["query_percent"]:.1f}% fewer'
            )

        if self.verbose:
            self.stdout.write(f'\nDetailed Queries: {current["queries"]}')

    def generate_summary_report(self, results):
        """Generate comprehensive summary report"""
        self.stdout.write(self.style.HTTP_INFO('\n=== PERFORMANCE SUMMARY REPORT ===\n'))
        
        total_improvements = []
        for endpoint, result in results.items():
            if 'improvement' in result:
                total_improvements.append(result['improvement']['time_percent'])
        
        if total_improvements:
            avg_improvement = statistics.mean(total_improvements)
            self.stdout.write(
                f'Average Performance Improvement: {avg_improvement:.1f}% faster\n'
            )

        # Performance recommendations
        self.stdout.write('RECOMMENDATIONS:')
        for endpoint, result in results.items():
            current = result['current']
            if current['avg_queries'] > 10:
                self.stdout.write(f'⚠️  {endpoint}: High query count ({current["avg_queries"]:.1f})')
            if current['avg_time'] > 1.0:
                self.stdout.write(f'⚠️  {endpoint}: Slow response time ({current["avg_time"]:.3f}s)')
            if 'improvement' in result and result['improvement']['time_percent'] > 50:
                self.stdout.write(f'✅ {endpoint}: Significant optimization opportunity')

    def generate_endpoint_report(self, endpoint, result):
        """Generate detailed report for specific endpoint"""
        self.stdout.write(f'\n=== {endpoint.upper()} DETAILED REPORT ===\n')
        self.print_benchmark_results(endpoint.replace('_', ' ').title(), result)
        
        # Additional analysis
        current = result['current']
        if current['avg_queries'] > 5:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  High database query count detected!'
                    f'\nConsider implementing:'
                    f'\n- select_related() for foreign keys'
                    f'\n- prefetch_related() for many-to-many relationships'
                    f'\n- Database indexing optimization'
                    f'\n- Query result caching'
                )
            )
        
        if current['avg_time'] > 0.5:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Slow response time detected!'
                    f'\nConsider implementing:'
                    f'\n- API response caching'
                    f'\n- Database query optimization'
                    f'\n- Pagination for large datasets'
                    f'\n- Asynchronous processing for heavy operations'
                )
            )