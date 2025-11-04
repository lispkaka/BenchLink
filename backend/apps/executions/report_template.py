"""
HTML测试报告模板
"""

HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {execution_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .summary-item {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .summary-item .label {{
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        
        .summary-item .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        
        .summary-item.passed .value {{
            color: #10b981;
        }}
        
        .summary-item.failed .value {{
            color: #ef4444;
        }}
        
        .summary-item.total .value {{
            color: #3b82f6;
        }}
        
        .summary-item.duration .value {{
            color: #8b5cf6;
            font-size: 24px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #1f2937;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        
        .testcase {{
            margin-bottom: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .testcase-header {{
            padding: 15px 20px;
            background: #f9fafb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .testcase-header:hover {{
            background: #f3f4f6;
        }}
        
        .testcase-header.passed {{
            border-left: 4px solid #10b981;
        }}
        
        .testcase-header.failed {{
            border-left: 4px solid #ef4444;
        }}
        
        .testcase-name {{
            font-weight: 600;
            color: #1f2937;
        }}
        
        .testcase-status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .testcase-status.passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .testcase-status.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .testcase-details {{
            padding: 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: none;
        }}
        
        .testcase.expanded .testcase-details {{
            display: block;
        }}
        
        .detail-row {{
            margin-bottom: 15px;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            padding: 10px;
            background: #f9fafb;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            overflow-x: auto;
        }}
        
        .assertions {{
            margin-top: 15px;
        }}
        
        .assertion {{
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 3px solid;
        }}
        
        .assertion.passed {{
            background: #d1fae5;
            border-color: #10b981;
        }}
        
        .assertion.failed {{
            background: #fee2e2;
            border-color: #ef4444;
        }}
        
        .assertion-type {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .assertion-message {{
            font-size: 13px;
            color: #4b5563;
        }}
        
        .error {{
            background: #fee2e2;
            border: 1px solid #fca5a5;
            border-radius: 4px;
            padding: 15px;
            color: #991b1b;
            margin-top: 15px;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }}
        
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .badge.method {{
            background: #dbeafe;
            color: #1e40af;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{execution_name}</h1>
            <div class="meta">
                <div>项目: {project_name}</div>
                <div>执行时间: {start_time}</div>
                <div>报告生成时间: {generated_time}</div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-item total">
                <div class="label">总用例数</div>
                <div class="value">{total_count}</div>
            </div>
            <div class="summary-item passed">
                <div class="label">通过</div>
                <div class="value">{passed_count}</div>
            </div>
            <div class="summary-item failed">
                <div class="label">失败</div>
                <div class="value">{failed_count}</div>
            </div>
            <div class="summary-item">
                <div class="label">通过率</div>
                <div class="value" style="color: {pass_rate_color};">{pass_rate}%</div>
            </div>
            <div class="summary-item duration">
                <div class="label">总耗时</div>
                <div class="value">{duration}s</div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">测试用例详情</div>
                {testcases_html}
            </div>
        </div>
        
        <div class="footer">
            <p>由 BenchLink 接口测试平台生成</p>
        </div>
    </div>
    
    <script>
        // 展开/折叠测试用例详情
        document.querySelectorAll('.testcase-header').forEach(header => {{
            header.addEventListener('click', function() {{
                this.parentElement.classList.toggle('expanded');
            }});
        }});
    </script>
</body>
</html>
"""


def generate_testcase_html(testcase_data):
    """生成单个测试用例的HTML"""
    status = testcase_data.get('status', 'unknown')
    result = testcase_data.get('result', {})
    
    # 生成断言HTML
    assertions_html = ''
    assertions = result.get('assertions', [])
    if assertions:
        assertions_html = '<div class="assertions"><div class="detail-label">断言结果</div>'
        for assertion in assertions:
            assertion_status = 'passed' if assertion.get('success') else 'failed'
            assertions_html += f'''
            <div class="assertion {assertion_status}">
                <div class="assertion-type">{assertion.get('type', 'unknown')}</div>
                <div class="assertion-message">{assertion.get('message', '')}</div>
            </div>
            '''
        assertions_html += '</div>'
    
    # 错误信息
    error_html = ''
    if result.get('error'):
        error_html = f'<div class="error"><strong>错误:</strong> {result.get("error")}</div>'
    
    # 响应体
    response_body = result.get('body', '')
    if len(response_body) > 1000:
        response_body = response_body[:1000] + '... (已截断)'
    
    # 方法标签
    method = testcase_data.get('method', 'GET')
    
    html = f'''
    <div class="testcase">
        <div class="testcase-header {status}">
            <div>
                <span class="testcase-name">{testcase_data.get('name', 'Unknown')}</span>
                <span class="badge method">{method}</span>
            </div>
            <span class="testcase-status {status}">{status.upper()}</span>
        </div>
        <div class="testcase-details">
            <div class="detail-row">
                <div class="detail-label">请求URL</div>
                <div class="detail-value">{result.get('url', 'N/A')}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">状态码</div>
                <div class="detail-value">{result.get('status_code', 'N/A')}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">响应时间</div>
                <div class="detail-value">{result.get('time', 0)} ms</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">响应体</div>
                <div class="detail-value"><pre>{response_body}</pre></div>
            </div>
            {assertions_html}
            {error_html}
        </div>
    </div>
    '''
    
    return html

