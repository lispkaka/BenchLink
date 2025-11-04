"""
性能测试执行器（基于 Locust）
"""
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class LocustExecutor:
    """Locust 性能测试执行器"""
    
    def __init__(self, performance_test):
        """
        初始化 Locust 执行器
        :param performance_test: PerformanceTest 实例
        """
        self.performance_test = performance_test
        self.api = performance_test.api
        self.environment = performance_test.environment
        self.variables = {}
        
        # 工作目录
        self.work_dir = Path(settings.BASE_DIR) / 'logs' / 'locust'
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    def _replace_variables(self, text: str) -> str:
        """替换变量 ${variable}"""
        if not text or not isinstance(text, str):
            return text
        
        vars_dict = self.variables.copy()
        if self.environment and self.environment.variables:
            vars_dict.update(self.environment.variables)
        
        import re
        def replace_match(match):
            var_name = match.group(1)
            return str(vars_dict.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{(\w+)\}', replace_match, text)
    
    def _replace_variables_in_dict(self, data: Any) -> Any:
        """递归替换字典中的变量"""
        if isinstance(data, dict):
            return {k: self._replace_variables_in_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables_in_dict(item) for item in data]
        elif isinstance(data, str):
            return self._replace_variables(data)
        else:
            return data
    
    def _build_url(self) -> str:
        """构建完整的请求 URL"""
        api_url = self.api.url.strip()
        
        # 如果已经是完整 URL，直接返回
        if api_url.startswith(('http://', 'https://')):
            return api_url
        
        # 如果有环境配置，使用环境的 base_url
        if self.environment and self.environment.base_url:
            base_url = self.environment.base_url.rstrip('/')
            api_url = api_url.lstrip('/')
            return f"{base_url}/{api_url}" if api_url else base_url
        
        raise ValueError(
            f"无法构建完整URL：接口URL是相对路径 '{api_url}'，"
            f"请配置测试环境的 base_url 或使用完整 URL。"
        )
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 合并环境默认请求头
        if self.environment and self.environment.headers:
            headers.update(self.environment.headers)
        
        # 使用接口定义的请求头
        if self.api.headers:
            headers.update(self.api.headers)
        
        # 替换变量
        headers = {k: self._replace_variables(str(v)) for k, v in headers.items()}
        
        return headers
    
    def _build_auth(self) -> Optional[Dict[str, str]]:
        """构建认证信息"""
        # 先尝试使用接口配置的认证
        if self.api.auth_type:
            auth_config = self.api.auth_config or {}
            
            if self.api.auth_type.lower() in ['bearer', 'token']:
                token = self._replace_variables(auth_config.get('token', ''))
                if token:
                    return {'Authorization': f'Bearer {token}'}
            elif self.api.auth_type.lower() == 'basic':
                username = self._replace_variables(auth_config.get('username', ''))
                password = self._replace_variables(auth_config.get('password', ''))
                if username and password:
                    import base64
                    credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
                    return {'Authorization': f'Basic {credentials}'}
        
        # 如果没有配置认证，尝试使用全局 Token
        from apps.environments.models import GlobalToken
        try:
            default_token = GlobalToken.objects.filter(is_active=True, is_default=True).first()
            if not default_token:
                default_token = GlobalToken.objects.filter(is_active=True).first()
            
            if default_token:
                token_value = default_token.token
                if default_token.variables:
                    for key, value in default_token.variables.items():
                        if key not in self.variables:
                            self.variables[key] = value
                token_value = self._replace_variables(token_value)
                
                if default_token.auth_type == 'bearer':
                    return {'Authorization': f'Bearer {token_value}'}
                elif default_token.auth_type == 'drf_token':
                    return {'Authorization': f'Token {token_value}'}
                elif default_token.auth_type == 'header':
                    header_name = default_token.header_name or 'Authorization'
                    token_format = default_token.token_format or 'Bearer'
                    return {header_name: f'{token_format} {token_value}' if token_format else token_value}
        except Exception as e:
            logger.warning(f"获取全局 Token 失败: {e}")
        
        return None
    
    def _generate_locustfile(self) -> str:
        """生成 Locust 测试脚本"""
        url = self._build_url()
        headers = self._build_headers()
        auth = self._build_auth()
        if auth:
            headers.update(auth)
        
        params = self._replace_variables_in_dict(self.api.params or {})
        body = self._replace_variables_in_dict(self.api.body or {}) if self.api.method in ['POST', 'PUT', 'PATCH'] else None
        
        # 转义 URL 和名称中的特殊字符
        escaped_url = url.replace('"', '\\"')
        escaped_name = self.api.name.replace('"', '\\"')
        
        # 构建 Locust 脚本
        locust_script = f"""# -*- coding: utf-8 -*-
from locust import HttpUser, task, between
import json

class BenchLinkUser(HttpUser):
    wait_time = between(0, 0)  # 不等待，立即执行
    
    def on_start(self):
        # 设置请求头
        headers = {json.dumps(headers, ensure_ascii=False, indent=8)}
        self.client.headers.update(headers)
    
    @task
    def api_request(self):
        # 构建请求参数
        params = {json.dumps(params, ensure_ascii=False, indent=8)}
        """
        
        if body:
            locust_script += f"""
        body = {json.dumps(body, ensure_ascii=False, indent=8)}
        
        # 发送请求
        response = self.client.{self.api.method.lower()}(
            "{escaped_url}",
            params=params,
            json=body,
            name="{escaped_name}"
        )
        """
        else:
            locust_script += f"""
        # 发送请求
        response = self.client.{self.api.method.lower()}(
            "{escaped_url}",
            params=params,
            name="{escaped_name}"
        )
        """
        
        # 保存脚本文件
        locust_file = self.work_dir / f'locustfile_{self.performance_test.id}_{int(timezone.now().timestamp())}.py'
        with open(locust_file, 'w', encoding='utf-8') as f:
            f.write(locust_script)
        
        return str(locust_file)
    
    def execute(self) -> Dict[str, Any]:
        """执行性能测试"""
        try:
            # 生成 Locust 脚本
            locust_file = self._generate_locustfile()
            
            # 创建输出目录
            output_dir = self.work_dir / f'result_{self.performance_test.id}_{int(timezone.now().timestamp())}'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            csv_prefix = output_dir / 'result'
            # Locust 2.x 使用 --html 参数时，如果指定的是文件路径，会生成单个HTML文件
            # 如果指定的是目录路径，会生成HTML报告目录
            html_report = output_dir / 'report.html'  # 单文件HTML报告
            html_report_dir = output_dir / 'report'  # HTML报告目录（备用）
            log_file = output_dir / 'locust.log'
            
            # 构建 Locust 命令
            threads = self.performance_test.threads
            ramp_up = self.performance_test.ramp_up
            duration = self.performance_test.duration
            
            # 提取 host（协议 + 域名）
            url = self._build_url()
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ''
            
            # 计算启动速率（每秒启动的用户数）
            spawn_rate = max(1, int(threads / ramp_up)) if ramp_up > 0 else threads
            
            cmd = [
                'locust',
                '-f', locust_file,  # Locust 脚本文件
                '--headless',  # 无头模式
                '--users', str(threads),  # 并发用户数
                '--spawn-rate', str(spawn_rate),  # 启动速率（每秒启动的用户数）
                '--host', host,  # 目标主机
                '--csv', str(csv_prefix),  # CSV 结果文件前缀
                '--html', str(html_report),  # HTML 报告（单文件）
                '--logfile', str(log_file),  # 日志文件
                '--loglevel', 'INFO',  # 日志级别
            ]
            
            # 如果设置了持续时间，使用 --run-time 参数
            if duration > 0:
                cmd.extend(['--run-time', f'{duration}s'])
            else:
                # 否则使用循环次数（Locust 默认运行直到停止）
                # 可以通过设置 --run-time 来实现循环次数
                loops = self.performance_test.loops
                if loops > 0:
                    # 估算时间：假设每个请求平均耗时 100ms
                    estimated_time = (loops * threads * 0.1)
                    cmd.extend(['--run-time', f'{int(estimated_time)}s'])
            
            logger.info(f"执行 Locust 命令: {' '.join(cmd)}")
            
            # 执行 Locust
            # 计算超时时间：测试持续时间 + 启动时间 + 额外缓冲时间（用于报告生成等）
            # 最小超时时间：如果duration为0，使用默认值
            if duration > 0:
                timeout_seconds = duration + ramp_up + 120  # 增加缓冲时间到120秒
            else:
                timeout_seconds = 600  # 默认10分钟超时
            
            logger.info(f"Locust 超时设置: {timeout_seconds}秒 (测试时长: {duration}s, 启动时间: {ramp_up}s)")
            
            start_time = timezone.now()
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired as e:
                logger.warning(f"Locust 执行超时: {e}")
                return {
                    'success': False,
                    'error': f'Locust 执行超时（超时时间: {timeout_seconds}秒，测试时长: {duration}秒，启动时间: {ramp_up}秒）。请检查测试配置或增加超时时间。'
                }
            end_time = timezone.now()
            
            # 解析结果
            # Locust 返回码规则：
            # 0: 所有请求都成功
            # 1: 有失败的请求（但执行本身是成功的，应该解析结果）
            # 2: 执行失败（配置错误、启动失败等）
            # 所以即使返回码非0，也要尝试解析结果，只要能够解析出结果就认为执行成功
            
            logger.info(f"Locust 执行完成，返回码: {result.returncode}")
            metrics = self._parse_results(csv_prefix, output_dir)
            
            # 检查解析结果是否有效
            if isinstance(metrics, dict) and 'error' in metrics:
                # 如果解析失败，且返回码非0，可能是真正的执行失败
                if result.returncode != 0:
                    logger.error(f"Locust 执行失败（返回码: {result.returncode}），且解析结果失败: {metrics.get('error')}")
                    return {
                        'success': False,
                        'error': metrics.get('error', 'Locust 执行失败且无法解析结果'),
                        'output': result.stdout,
                        'log': result.stderr,
                        'returncode': result.returncode
                    }
                else:
                    logger.error(f"解析结果失败: {metrics.get('error')}")
                    return {
                        'success': False,
                        'error': metrics.get('error', '解析结果失败'),
                        'output': result.stdout,
                        'log': result.stderr
                    }
            
            # 如果返回码是2，通常是配置错误或启动失败，即使能解析结果也认为是失败
            if result.returncode == 2:
                logger.error(f"Locust 配置错误或启动失败（返回码: 2）")
                return {
                    'success': False,
                    'error': result.stderr or result.stdout or 'Locust 配置错误或启动失败',
                    'output': result.stdout,
                    'log': result.stderr,
                    'returncode': result.returncode
                }
            
            # 计算实际运行时间（从开始到结束）
            actual_duration = (end_time - start_time).total_seconds()
            
            # 验证请求数计算的合理性
            # Locust的--run-time包括启动时间，所以实际满负载运行时间 = duration - ramp_up
            # 平均RPS = 总请求数 / 实际运行时间
            if metrics.get('total_samples', 0) > 0:
                calculated_rps = metrics['total_samples'] / actual_duration if actual_duration > 0 else 0
                reported_rps = metrics.get('throughput', 0)
                
                # 如果计算的RPS和报告的RPS差异较大，记录警告
                if abs(calculated_rps - reported_rps) > reported_rps * 0.1 and reported_rps > 0:
                    logger.warning(
                        f"RPS计算差异较大: 计算值={calculated_rps:.2f}, 报告值={reported_rps:.2f}, "
                        f"总请求数={metrics['total_samples']}, 实际运行时间={actual_duration:.2f}秒"
                    )
                
                # 添加详细统计信息
                metrics['actual_duration'] = actual_duration  # 实际运行时间（秒）
                metrics['ramp_up_time'] = ramp_up  # 启动时间（秒）
                metrics['full_load_duration'] = max(0, actual_duration - ramp_up)  # 满负载运行时间（秒）
                metrics['calculated_rps'] = calculated_rps  # 根据总请求数和实际时间计算的RPS
                
                logger.info(
                    f"性能测试统计: 总请求数={metrics['total_samples']}, "
                    f"失败请求数={metrics.get('failed_samples', 0)}, "
                    f"实际运行时间={actual_duration:.2f}秒, "
                    f"满负载运行时间={metrics['full_load_duration']:.2f}秒, "
                    f"平均RPS={reported_rps:.2f}, 计算RPS={calculated_rps:.2f}"
                )
            
            # 检查 stderr 是否包含真正的错误（不是 Locust 的正常统计输出）
            error_msg = None
            if result.stderr:
                # Locust 的正常统计输出不应该被视为错误
                # 只有包含 "Error"、"Exception"、"Traceback" 等关键字才认为是错误
                stderr_lower = result.stderr.lower()
                if any(keyword in stderr_lower for keyword in ['error', 'exception', 'traceback', 'failed', 'failure']):
                    # 检查是否真的是错误（不是统计信息中的 "0(0.00%)" 这种）
                    if not any(pattern in result.stderr for pattern in ['0(0.00%)', 'Type Name', '# reqs', 'req/s', 'Aggregated']):
                        error_msg = result.stderr
            
            # 从 stdout 中提取错误信息（Locust 会将错误报告输出到 stdout）
            if not error_msg and result.stdout:
                # 检查是否有 "Error report" 部分
                if 'Error report' in result.stdout:
                    # 提取错误信息（但不作为失败标志，因为这是正常的测试结果）
                    # 错误信息已经包含在 metrics 中，这里只作为日志记录
                    pass
            
            # 检查HTML报告是否存在
            # Locust 2.x 使用 --html 参数生成单个HTML文件
            html_report_path = None
            if html_report.exists():
                html_report_path = str(html_report)
            else:
                # 如果单文件不存在，尝试查找HTML报告目录（某些版本可能生成目录）
                html_report_dir = output_dir / 'report'
                if html_report_dir.exists():
                    index_file = html_report_dir / 'index.html'
                    if index_file.exists():
                        html_report_path = str(index_file)
            
            # 即使有失败的请求，只要执行成功完成，就返回成功
            # 失败的请求信息已经在 metrics 中记录
            return {
                'success': True,
                'locust_file': locust_file,
                'html_report': html_report_path,
                'csv_prefix': str(csv_prefix),
                'metrics': metrics,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': actual_duration,
                'output': result.stdout,
                'error': error_msg,  # 只在真正有错误时返回（配置错误等）
                'log': result.stderr,  # 将 Locust 的正常输出作为日志
                'returncode': result.returncode  # 记录返回码，便于调试
            }
        
        except Exception as e:
            logger.exception(f"执行性能测试失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_results(self, csv_prefix: Path, output_dir: Path) -> Dict[str, Any]:
        """解析 Locust 结果文件"""
        try:
            import csv
            
            metrics = {
                'total_samples': 0,
                'success_samples': 0,
                'failed_samples': 0,
                'response_times': [],
                'min_response_time': None,
                'max_response_time': None,
                'avg_response_time': None,
                'median_response_time': None,
                'p90_response_time': None,
                'p95_response_time': None,
                'p99_response_time': None,
                'throughput': 0,
                'error_rate': 0
            }
            
            # 读取统计结果
            stats_file = Path(f'{csv_prefix}_stats.csv')
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    # Locust 2.x CSV格式：最后一行是 "Aggregated" 汇总行
                    # 优先读取汇总行，如果没有则使用第一行
                    aggregated_row = None
                    all_rows = list(reader)
                    
                    # 查找 Aggregated 行（Type为空或Name为Aggregated）
                    for row in all_rows:
                        row_name = row.get('Name', '').strip()
                        row_type = row.get('Type', '').strip()
                        if row_name == 'Aggregated' or (not row_type and not row_name):
                            aggregated_row = row
                            break
                    
                    # 如果没有找到Aggregated行，使用最后一行（通常是汇总）
                    if not aggregated_row and all_rows:
                        aggregated_row = all_rows[-1]
                    
                    if aggregated_row:
                        try:
                            # 解析各个字段
                            metrics['total_samples'] = int(aggregated_row.get('Request Count', aggregated_row.get('# requests', 0)) or 0)
                            metrics['failed_samples'] = int(aggregated_row.get('Failure Count', aggregated_row.get('# failures', 0)) or 0)
                            metrics['success_samples'] = metrics['total_samples'] - metrics['failed_samples']
                            
                            # 响应时间（毫秒）- Locust 存储的是毫秒
                            metrics['avg_response_time'] = float(aggregated_row.get('Average Response Time', aggregated_row.get('Average', 0)) or 0)
                            metrics['min_response_time'] = float(aggregated_row.get('Min Response Time', aggregated_row.get('Min', 0)) or 0)
                            metrics['max_response_time'] = float(aggregated_row.get('Max Response Time', aggregated_row.get('Max', 0)) or 0)
                            
                            # RPS (Requests Per Second)
                            metrics['throughput'] = float(aggregated_row.get('Requests/s', aggregated_row.get('RPS', 0)) or 0)
                            
                            # 百分位数（Locust 2.x 使用列名如 '50%', '90%', '95%', '99%'）
                            metrics['median_response_time'] = float(aggregated_row.get('50%', aggregated_row.get('Median', metrics['avg_response_time'])) or metrics['avg_response_time'])
                            metrics['p90_response_time'] = float(aggregated_row.get('90%', metrics['max_response_time']) or metrics['max_response_time'])
                            metrics['p95_response_time'] = float(aggregated_row.get('95%', metrics['max_response_time']) or metrics['max_response_time'])
                            metrics['p99_response_time'] = float(aggregated_row.get('99%', metrics['max_response_time']) or metrics['max_response_time'])
                            
                        except (ValueError, TypeError) as e:
                            logger.warning(f"解析 CSV 汇总行数据失败: {e}, row: {aggregated_row}")
                    else:
                        logger.warning(f"未找到 CSV 汇总行数据")
            
            # 计算错误率
            if metrics['total_samples'] > 0:
                metrics['error_rate'] = (metrics['failed_samples'] / metrics['total_samples']) * 100
            
            # 如果某些指标缺失，使用默认值
            if metrics['p90_response_time'] is None:
                metrics['p90_response_time'] = metrics['max_response_time'] or 0
            if metrics['p95_response_time'] is None:
                metrics['p95_response_time'] = metrics['max_response_time'] or 0
            if metrics['p99_response_time'] is None:
                metrics['p99_response_time'] = metrics['max_response_time'] or 0
            
            return metrics
        
        except Exception as e:
            logger.exception(f"解析 Locust 结果失败: {e}")
            return {
                'error': f'解析结果失败: {str(e)}'
            }

