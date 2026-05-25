import httpx
from app.config.settings import get_settings


class CommunityClient:
    """队友社区系统 API Client。

    负责调用队友开发的社区系统接口，目前为骨架代码，
    等待队友提供实际 API 地址后进行联调。
    """

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.community_service_base_url.rstrip("/")
        self.api_key = settings.community_service_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=30.0,
            )
        return self._client

    async def create_task(self, task_data: dict) -> dict:
        """调用队友社区接口创建正式互助任务。

        Args:
            task_data: 任务数据，包含 title, description, task_type, tags, external_user_id 等

        Returns:
            队友返回的 created_task 对象
        """
        client = await self._get_client()
        try:
            response = await client.post("/tasks", json=task_data)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": "无法连接社区服务，请确认社区服务已启动。"}
        except Exception as e:
            return {"error": str(e)}

    async def get_user_info(self, external_user_id: str) -> dict:
        """获取用户基本信息。"""
        client = await self._get_client()
        try:
            response = await client.get(f"/users/{external_user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": "无法连接社区服务。"}
        except Exception as e:
            return {"error": str(e)}

    async def get_post(self, post_id: str) -> dict:
        """获取社区帖子详情。"""
        client = await self._get_client()
        try:
            response = await client.get(f"/posts/{post_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


community_client = CommunityClient()
