"""
Email sender executor using yagmail (wrapper over SMTP).
Supports QQ, 163, and Gmail SMTP servers.
"""
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from .base import BaseExecutor, WorkflowExecutionError


class EmailSenderExecutor(BaseExecutor):

    SMTP_SERVERS = {
        "qq": {"host": "smtp.qq.com", "port": 465},
        "163": {"host": "smtp.163.com", "port": 465},
        "gmail": {"host": "smtp.gmail.com", "port": 587},
    }

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "title": "邮件发送配置",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "邮件服务商",
                    "enum": ["qq", "163", "gmail", "custom"],
                    "default": "qq",
                },
                "smtp_host": {
                    "type": "string",
                    "title": "SMTP服务器",
                    "description": "自定义SMTP服务器地址（provider为custom时使用）",
                    "default": "",
                },
                "smtp_port": {
                    "type": "number",
                    "title": "SMTP端口",
                    "default": 465,
                },
                "smtp_user": {
                    "type": "string",
                    "title": "发件人邮箱",
                    "description": "SMTP登录用户名/邮箱地址",
                },
                "smtp_password": {
                    "type": "string",
                    "title": "SMTP密码/授权码",
                    "description": "QQ邮箱使用授权码，Gmail使用应用专用密码",
                },
                "to": {
                    "type": "string",
                    "title": "收件人",
                    "description": "多个收件人用逗号分隔",
                },
                "subject": {
                    "type": "string",
                    "title": "邮件主题",
                },
                "body": {
                    "type": "string",
                    "title": "邮件正文",
                    "description": "支持${node_id.field}表达式引用上游数据",
                },
                "is_html": {
                    "type": "boolean",
                    "title": "HTML格式",
                    "description": "正文是否为HTML格式",
                    "default": True,
                },
                "cc": {
                    "type": "string",
                    "title": "抄送(CC)",
                    "description": "多个地址用逗号分隔",
                    "default": "",
                },
                "bcc": {
                    "type": "string",
                    "title": "密送(BCC)",
                    "default": "",
                },
                "attachments": {
                    "type": "array",
                    "title": "附件路径列表",
                    "description": "本地文件路径或表达式",
                    "items": {"type": "string"},
                },
                "dry_run": {
                    "type": "boolean",
                    "title": "测试模式",
                    "description": "开启后不会真正发送邮件",
                    "default": False,
                },
                "max_retries": {
                    "type": "number",
                    "title": "最大重试次数",
                    "default": 3,
                },
                "retry_interval": {
                    "type": "number",
                    "title": "重试间隔(秒)",
                    "default": 5,
                },
            },
            "required": ["smtp_user", "smtp_password", "to", "subject", "body"],
        }

    def execute(self, config: dict, context: dict) -> dict:
        provider = config.get("provider", "qq")
        smtp_user = config.get("smtp_user", "")
        smtp_password = config.get("smtp_password", "")
        to_str = config.get("to", "")
        subject = config.get("subject", "")
        body = config.get("body", "")
        is_html = config.get("is_html", True)
        cc = config.get("cc", "")
        bcc = config.get("bcc", "")
        attachments = config.get("attachments", [])
        dry_run = config.get("dry_run", False)
        max_retries = config.get("max_retries", 3)
        retry_interval = config.get("retry_interval", 5)

        # Resolve SMTP settings
        if provider in self.SMTP_SERVERS:
            smtp_host = self.SMTP_SERVERS[provider]["host"]
            smtp_port = self.SMTP_SERVERS[provider]["port"]
        else:
            smtp_host = config.get("smtp_host", "smtp.qq.com")
            smtp_port = config.get("smtp_port", 465)

        # Resolve expressions in subject, body, attachments
        subject = self._resolve_string(subject, context)
        body = self._resolve_string(body, context)
        to_str = self._resolve_string(to_str, context)

        # Parse recipients
        to_list = [addr.strip() for addr in to_str.split(",") if addr.strip()]
        cc_list = [addr.strip() for addr in cc.split(",") if addr.strip()] if cc else []
        bcc_list = [addr.strip() for addr in bcc.split(",") if addr.strip()] if bcc else []

        # Resolve attachment paths
        resolved_attachments = []
        for att in attachments:
            att = self._resolve_string(att, context)
            if os.path.exists(att):
                resolved_attachments.append(att)

        if dry_run:
            return {
                "status": "success",
                "data": {
                    "sent_to": to_list,
                    "cc": cc_list,
                    "bcc": bcc_list,
                    "subject": subject,
                    "attachments": resolved_attachments,
                    "dry_run": True,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }

        # Build email
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)

        body_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, body_type, "utf-8"))

        # Attach files
        for filepath in resolved_attachments:
            try:
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(filepath)
                    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                    msg.attach(part)
            except Exception as e:
                raise WorkflowExecutionError(
                    "ATTACH_ERROR", f"Failed to attach file {filepath}: {e}", "email_sender"
                )

        all_recipients = to_list + cc_list + bcc_list

        # Send with retry
        last_error = None
        use_ssl = smtp_port == 465

        for attempt in range(max_retries):
            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                    server.starttls()

                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, all_recipients, msg.as_string())
                server.quit()

                return {
                    "status": "success",
                    "data": {
                        "sent_to": to_list,
                        "subject": subject,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "attachment_count": len(resolved_attachments),
                    },
                }
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)

        raise WorkflowExecutionError(
            "SEND_ERROR",
            f"Failed to send email after {max_retries} attempts: {last_error}",
            "email_sender",
        )

    @staticmethod
    def _resolve_string(value: str, context: dict) -> str:
        import re
        pattern = re.compile(r'\$\{(\w+)\.(.+?)\}')
        def replacer(match):
            node_id = match.group(1)
            field_path = match.group(2)
            if node_id in context:
                result = _get_nested(context[node_id], field_path)
                if result is not None:
                    return str(result)
            return match.group(0)
        return pattern.sub(replacer, value)


def _get_nested(data, path: str):
    import re
    parts = re.split(r'\.|\[|\]', path)
    current = data
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            if isinstance(current, list):
                current = current[int(part)]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
