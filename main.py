from typing import Optional, List, Dict, Any

from core.plugin import BasePlugin, logger, register_tool
from core.chat import KiraMessageBatchEvent


BUILTIN_PLUGIN_IDS = {
    "kira_builtin_plugin",
    "kira_debounce_plugin",
    "kira_session_plugin",
    "kira_plugin_simple_memory",
    "search",
    "file",
}


class PluginManagerPlugin(BasePlugin):
    def __init__(self, ctx, cfg: dict):
        super().__init__(ctx, cfg)
        self.owner_id: str = ""
        self.admin_ids: List[str] = []
        self.show_builtin_plugins: bool = False

    async def initialize(self):
        logger.info("Initializing Plugin Manager Plugin")
        self.owner_id = str(self.plugin_cfg.get("owner_id", "") or "")
        self.admin_ids = [
            str(user_id) for user_id in self.plugin_cfg.get("admin_ids", []) if user_id
        ]
        self.show_builtin_plugins = bool(self.plugin_cfg.get("show_builtin_plugins", False))
        logger.info(f"Plugin Manager initialized. Owner: {self.owner_id}, Admins: {self.admin_ids}, Show builtin: {self.show_builtin_plugins}")

    async def terminate(self):
        pass

    def _is_admin(self, event: KiraMessageBatchEvent) -> bool:
        if not self.owner_id and not self.admin_ids:
            return True
        try:
            sender_id = str(event.messages[-1].sender.user_id)
            if sender_id == self.owner_id:
                return True
            if sender_id in self.admin_ids:
                return True
            return False
        except (AttributeError, IndexError, TypeError) as e:
            logger.warning(f"Failed to get sender user_id: {e}")
            return False

    def _get_plugins(self) -> Dict[str, Dict[str, Any]]:
        if not self.ctx.plugin_mgr:
            return {}
        registered = self.ctx.plugin_mgr.get_registered_plugins()
        plugins = {}
        for plugin_id in registered.keys():
            if not self.show_builtin_plugins and plugin_id in BUILTIN_PLUGIN_IDS:
                continue
            manifest = self.ctx.plugin_mgr.get_plugin_manifest(plugin_id) or {}
            enabled = self.ctx.plugin_mgr.is_plugin_enabled(plugin_id)
            is_builtin = plugin_id in BUILTIN_PLUGIN_IDS
            plugins[plugin_id] = {
                "id": plugin_id,
                "display_name": manifest.get("display_name") or plugin_id,
                "version": str(manifest.get("version") or ""),
                "author": str(manifest.get("author") or ""),
                "description": str(manifest.get("description") or ""),
                "enabled": enabled,
                "is_builtin": is_builtin,
            }
        return plugins

    def _match_plugin(self, plugin_name: str) -> Optional[str]:
        plugins = self._get_plugins()
        if not plugin_name:
            return None
        plugin_name_lower = plugin_name.lower().strip()
        for plugin_id, info in plugins.items():
            if plugin_id.lower() == plugin_name_lower:
                return plugin_id
            display_name = str(info.get("display_name", "")).lower()
            if display_name == plugin_name_lower:
                return plugin_id
        matches = []
        for plugin_id, info in plugins.items():
            display_name = str(info.get("display_name", "")).lower()
            if plugin_name_lower in plugin_id.lower() or plugin_name_lower in display_name:
                matches.append(plugin_id)
        if len(matches) == 1:
            return matches[0]
        return None

    def _format_plugin_list(self, plugins: Dict[str, Dict[str, Any]]) -> str:
        if not plugins:
            return "当前没有安装任何插件"
        if self.show_builtin_plugins:
            title = "插件列表（含内置）："
        else:
            title = "用户插件列表："
        lines = [title, ""]
        sorted_plugins = sorted(plugins.items(), key=lambda x: x[1].get("display_name", x[0]))
        for idx, (plugin_id, info) in enumerate(sorted_plugins, 1):
            display_name = info.get("display_name", plugin_id)
            status = "已启用" if info.get("enabled") else "未启用"
            lines.append(f"{idx}.{display_name} [{plugin_id}] {status}")
        return "\n".join(lines)

    def _format_plugin_info(self, plugin_id: str, info: Dict[str, Any]) -> str:
        display_name = info.get("display_name", plugin_id)
        status = "已启用" if info.get("enabled") else "未启用"
        version = info.get("version", "未知")
        author = info.get("author", "未知")
        description = info.get("description", "暂无描述")
        plugin_type = "内置插件" if info.get("is_builtin") else "用户插件"
        lines = [
            f"插件名称：{display_name}",
            f"插件ID：{plugin_id}",
            f"类型：{plugin_type}",
            f"状态：{status}",
            f"版本：{version}",
            f"作者：{author}",
            f"描述：{description}",
        ]
        return "\n".join(lines)

    @register_tool(
        name="list_plugins",
        description="列出所有已安装的插件。返回插件名称、ID和当前状态。根据配置决定是否包含内置核心插件。",
        params={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
    async def list_plugins(self, event: KiraMessageBatchEvent) -> str:
        plugins = self._get_plugins()
        return self._format_plugin_list(plugins)

    @register_tool(
        name="enable_plugin",
        description="启用指定的用户插件。只有管理员才能执行此操作。参数可以是插件ID或插件名称，支持模糊匹配。注意：内置插件无法通过此工具启停。",
        params={
            "type": "object",
            "properties": {
                "plugin_name": {
                    "type": "string",
                    "description": "要启用的插件名称或ID'"
                }
            },
            "required": ["plugin_name"]
        }
    )
    async def enable_plugin(self, event: KiraMessageBatchEvent, plugin_name: str) -> str:
        if not self._is_admin(event):
            return "权限不足，只有管理员才能执行此操作"
        plugin_id = self._match_plugin(plugin_name)
        if not plugin_id:
            return f"未找到匹配的插件：{plugin_name}"
        plugins = self._get_plugins()
        info = plugins.get(plugin_id, {})
        if info.get("is_builtin"):
            return "内置插件无法通过此工具启停"
        if not self.ctx.plugin_mgr:
            return "插件管理器不可用"
        current_status = self.ctx.plugin_mgr.is_plugin_enabled(plugin_id)
        if current_status:
            display_name = info.get("display_name", plugin_id)
            return f"插件 {display_name} 已经是启用状态"
        await self.ctx.plugin_mgr.set_plugin_enabled(plugin_id, True)
        display_name = info.get("display_name", plugin_id)
        return f"已启用插件：{display_name}"

    @register_tool(
        name="disable_plugin",
        description="禁用指定的用户插件。只有管理员才能执行此操作。参数可以是插件ID或插件名称，支持模糊匹配。注意：内置插件无法通过此工具启停。",
        params={
            "type": "object",
            "properties": {
                "plugin_name": {
                    "type": "string",
                    "description": "要禁用的插件名称或ID"
                }
            },
            "required": ["plugin_name"]
        }
    )
    async def disable_plugin(self, event: KiraMessageBatchEvent, plugin_name: str) -> str:
        if not self._is_admin(event):
            return "权限不足，只有管理员才能执行此操作"
        plugin_id = self._match_plugin(plugin_name)
        if not plugin_id:
            return f"未找到匹配的插件：{plugin_name}"
        plugins = self._get_plugins()
        info = plugins.get(plugin_id, {})
        if info.get("is_builtin"):
            return "内置插件无法通过此工具启停"
        if not self.ctx.plugin_mgr:
            return "插件管理器不可用"
        current_status = self.ctx.plugin_mgr.is_plugin_enabled(plugin_id)
        if not current_status:
            display_name = info.get("display_name", plugin_id)
            return f"插件 {display_name} 已经是禁用状态"
        await self.ctx.plugin_mgr.set_plugin_enabled(plugin_id, False)
        display_name = info.get("display_name", plugin_id)
        return f"已禁用插件：{display_name}"

    @register_tool(
        name="get_plugin_info",
        description="获取指定插件的详细信息，包括名称、ID、类型、状态、版本、作者和描述。",
        params={
            "type": "object",
            "properties": {
                "plugin_name": {
                    "type": "string",
                    "description": "要查询的插件名称或ID"
                }
            },
            "required": ["plugin_name"]
        }
    )
    async def get_plugin_info(self, event: KiraMessageBatchEvent, plugin_name: str) -> str:
        plugin_id = self._match_plugin(plugin_name)
        if not plugin_id:
            return f"未找到匹配的插件：{plugin_name}"
        plugins = self._get_plugins()
        info = plugins.get(plugin_id)
        if not info:
            return f"未找到插件：{plugin_name}"
        return self._format_plugin_info(plugin_id, info)
