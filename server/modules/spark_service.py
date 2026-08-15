"""讯飞星火 WebSocket 客户端，密钥仅从环境变量读取。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urlencode, urlparse

from websocket import WebSocketException, WebSocketTimeoutException, create_connection
from ..db.system_repository import SystemRepository


class SparkConfigurationError(RuntimeError):
    pass


class SparkAPIError(RuntimeError):
    pass


class SparkService:
    def __init__(self) -> None:
        self.system = SystemRepository()
        self.url = os.getenv("SPARKAI_URL", "wss://spark-api.xf-yun.com/v3.1/chat")
        self.app_id = os.getenv("SPARKAI_APP_ID", "")
        self.api_secret = os.getenv("SPARKAI_API_SECRET", "")
        self.api_key = os.getenv("SPARKAI_API_KEY", "")
        self.domain = os.getenv("SPARKAI_DOMAIN", "generalv3")

    @property
    def configured(self) -> bool:
        return all((self.url, self.app_id, self.api_secret, self.api_key, self.domain))

    def _authenticated_url(self) -> str:
        if not self.configured:
            raise SparkConfigurationError("星火密钥尚未配置，请检查 server/.env。")

        parsed = urlparse(self.url)
        date = format_datetime(datetime.now(timezone.utc), usegmt=True)
        signature_origin = f"host: {parsed.netloc}\ndate: {date}\nGET {parsed.path} HTTP/1.1"
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode("utf-8")
        ).decode("utf-8")
        return f"{self.url}?{urlencode({'authorization': authorization, 'date': date, 'host': parsed.netloc})}"

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.55,
        max_tokens: int = 2048,
        uid: str = "moss-user",
    ) -> str:
        if not self.system.enabled("spark_enabled"):
            raise SparkConfigurationError("管理员已暂停讯飞星火服务。")
        payload = {
            "header": {"app_id": self.app_id, "uid": uid[:32]},
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": temperature,
                    "top_k": 4,
                    "max_tokens": max_tokens,
                }
            },
            "payload": {"message": {"text": messages[-12:]}},
        }

        answer_parts: list[str] = []
        socket = None
        try:
            socket = create_connection(self._authenticated_url(), timeout=45)
            socket.send(json.dumps(payload, ensure_ascii=False))
            while True:
                response = json.loads(socket.recv())
                header = response.get("header", {})
                if header.get("code", 0) != 0:
                    raise SparkAPIError(
                        f"星火接口错误 {header.get('code')}：{header.get('message', '未知错误')}"
                    )
                choices = response.get("payload", {}).get("choices", {})
                for item in choices.get("text", []):
                    answer_parts.append(item.get("content", ""))
                if header.get("status") == 2 or choices.get("status") == 2:
                    break
        except WebSocketTimeoutException as exc:
            self.system.log("spark", "星火响应超时")
            raise SparkAPIError("星火响应超时，请稍后重试。") from exc
        except (OSError, WebSocketException) as exc:
            self.system.log("spark", "星火网络连接失败")
            raise SparkAPIError("无法连接讯飞星火服务，请检查网络。") from exc
        except json.JSONDecodeError as exc:
            self.system.log("spark", "星火返回数据无法解析")
            raise SparkAPIError("星火返回了无法解析的数据。") from exc
        finally:
            if socket is not None:
                socket.close()

        answer = "".join(answer_parts).strip()
        if not answer:
            raise SparkAPIError("星火返回了空内容。")
        return answer
