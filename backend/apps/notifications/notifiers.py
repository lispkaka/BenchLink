"""
通知发送器
"""
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime


class BaseNotifier:
    """通知基类"""
    
    def send(self, execution, channel):
        """发送通知"""
        message = self.format_message(execution)
        return self.do_send(message, channel)
    
    def format_message(self, execution):
        """格式化消息"""
        raise NotImplementedError
    
    def do_send(self, message, channel):
        """发送消息"""
        raise NotImplementedError


class WeComNotifier(BaseNotifier):
    """企业微信通知器"""
    
    def format_message(self, execution):
        """格式化为企业微信Markdown消息"""
        # 状态图标和文字
        if execution.status == 'passed':
            status_icon = '✅'
            status_text = '通过'
        elif execution.status == 'failed':
            status_icon = '❌'
            status_text = '失败'
        else:
            status_icon = '⏸️'
            status_text = execution.get_status_display()
        
        # 基本信息
        project_name = execution.project.name if execution.project else '-'
        suite_name = execution.testsuite.name if execution.testsuite else '-'
        testcase_name = execution.testcase.name if execution.testcase else '-'
        
        # 执行结果统计
        result = execution.result or {}
        total = result.get('total', 1)
        passed = result.get('passed', 1 if execution.status == 'passed' else 0)
        failed = result.get('failed', 0 if execution.status == 'passed' else 1)
        pass_rate = result.get('pass_rate', 100 if execution.status == 'passed' else 0)
        
        # 执行时间
        start_time = execution.start_time.strftime('%Y-%m-%d %H:%M:%S') if execution.start_time else '-'
        duration = f"{execution.duration:.2f}s" if execution.duration else '-'
        
        # 执行人
        executor = execution.executor.username if execution.executor else '-'
        
        # 详情链接（需要配置前端地址）
        detail_url = f"http://localhost:8080/executions/{execution.id}"
        
        # 构建Markdown消息
        markdown_content = f"""## {status_icon} 测试执行通知

**项目：** {project_name}
**套件：** {suite_name}
{"**用例：** " + testcase_name if testcase_name != '-' else ""}
**状态：** {status_text}

---

### 📊 执行结果
- 总用例数：{total}
- 通过：<font color="info">{passed}</font>
- 失败：<font color="warning">{failed}</font>
- 通过率：**{pass_rate}%**
- 执行时长：{duration}

### 📝 执行信息
- 执行人：{executor}
- 开始时间：{start_time}

[点击查看详情]({detail_url})
"""
        
        return markdown_content
    
    def do_send(self, message, channel):
        """发送企业微信消息"""
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
            
            response = requests.post(
                channel.webhook_url,
                json=data,
                timeout=10
            )
            
            result = response.json()
            if result.get('errcode') == 0:
                return True, '发送成功'
            else:
                return False, f"发送失败: {result.get('errmsg', '未知错误')}"
                
        except Exception as e:
            return False, f'发送异常: {str(e)}'


class DingTalkNotifier(BaseNotifier):
    """钉钉通知器（支持加签）"""
    
    def generate_sign(self, secret):
        """生成钉钉加签"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return timestamp, sign
    
    def format_message(self, execution):
        """格式化为钉钉Markdown消息"""
        # 与企业微信类似，但格式稍有不同
        if execution.status == 'passed':
            status_text = '✅ 通过'
        elif execution.status == 'failed':
            status_text = '❌ 失败'
        else:
            status_text = f'⏸️ {execution.get_status_display()}'
        
        project_name = execution.project.name if execution.project else '-'
        suite_name = execution.testsuite.name if execution.testsuite else '-'
        
        result = execution.result or {}
        total = result.get('total', 1)
        passed = result.get('passed', 1 if execution.status == 'passed' else 0)
        failed = result.get('failed', 0 if execution.status == 'passed' else 1)
        pass_rate = result.get('pass_rate', 100 if execution.status == 'passed' else 0)
        
        duration = f"{execution.duration:.2f}s" if execution.duration else '-'
        detail_url = f"http://localhost:8080/executions/{execution.id}"
        
        markdown_text = f"""## 测试执行通知

**状态：** {status_text}

**项目：** {project_name}  
**套件：** {suite_name}

**执行结果：**  
总用例数：{total} | 通过：{passed} | 失败：{failed}  
通过率：{pass_rate}% | 耗时：{duration}

[查看详情]({detail_url})
"""
        return markdown_text
    
    def do_send(self, message, channel):
        """发送钉钉消息"""
        try:
            url = channel.webhook_url
            
            # 如果有加签密钥，生成签名
            if channel.secret:
                timestamp, sign = self.generate_sign(channel.secret)
                url = f"{url}&timestamp={timestamp}&sign={sign}"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "测试执行通知",
                    "text": message
                }
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                return True, '发送成功'
            else:
                return False, f"发送失败: {result.get('errmsg', '未知错误')}"
                
        except Exception as e:
            return False, f'发送异常: {str(e)}'


# 通知器工厂
NOTIFIERS = {
    'wecom': WeComNotifier(),
    'dingtalk': DingTalkNotifier(),
}


def get_notifier(channel_type):
    """获取通知器实例"""
    return NOTIFIERS.get(channel_type)




