# 插件查询管理插件 (Plugin Manager)

一个为 KiraAI 聊天机器人开发的插件管理插件，让 AI 能够感知已安装的插件，并支持通过自然语言查询和启停插件。

## 功能特性

- ✅ 列出所有已安装的用户插件
- ✅ 可选显示内置核心插件
- ✅ 启用/禁用指定插件
- ✅ 获取插件详细信息
- ✅ 支持插件名称模糊匹配
- ✅ 基于用户 ID 的权限控制（支持 QQ、Telegram 等多平台）
- ✅ 内置插件保护（无法通过工具启停）

## 安装

### 1. 安装插件

将插件文件夹 `plugin_manager` 复制到 KiraAI 的 `data/plugins` 目录下。

```
data/plugins/plugin_manager/
├── __init__.py
├── main.py
├── manifest.json
└── schema.json
```

### 2. 配置插件

在 KiraAI 的 WebUI 配置页面或 `data/config/plugins/plugin_manager.json` 中配置：

```json
{
  "owner_id": "",
  "admin_ids": [],
  "show_builtin_plugins": false
}
```

### 3. 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `owner_id` | 字符串 | "" | 所有者的用户ID（支持QQ号、Telegram用户ID等），拥有启停插件的最高权限 |
| `admin_ids` | 列表 | [] | 管理员的用户ID列表，同样拥有启停插件的权限 |
| `show_builtin_plugins` | 布尔值 | false | 开启后查询插件列表时将包含内置核心插件，关闭则只显示用户插件 |

## 使用示例

### 查询插件列表

用户可以通过自然语言查询已安装的插件：

```
用户: 有哪些插件
Bot: 用户插件列表：

1.QQ空间助手 [qzone_plugin] 已启用
2.天气查询 [weather] 已启用
3.插件查询 [plugin_manager] 已启用
4.系统信息插件 [system_info_plugin] 未启用
```

### 启用插件

管理员可以通过自然语言启用插件：

```
用户: 把系统信息插件打开
Bot: 已启用插件：系统信息插件
```

### 禁用插件

管理员可以通过自然语言禁用插件：

```
用户: 把天气插件关了
Bot: 已禁用插件：天气查询
```

### 查询插件详情

```
用户: 天气插件是什么
Bot: 插件名称：天气查询
插件ID：weather
类型：用户插件
状态：已启用
版本：1.0.5
作者：Levi.A
描述：一个天气查询插件，通过从 weather.com.cn 网站抓取数据，提供中国城市的天气信息。
```

## 权限控制

插件支持基于用户 ID 的权限控制，兼容多平台：

### 权限级别

1. **普通用户**：
   - 可以查询插件列表
   - 可以查询插件详情
   - 不能启停插件

2. **管理员**（通过 `admin_ids` 配置）：
   - 可以查询插件列表
   - 可以查询插件详情
   - 可以启停用户插件

3. **所有者**（通过 `owner_id` 配置）：
   - 拥有管理员所有权限
   - 最高权限级别

### 平台兼容性

| 平台 | 用户ID类型 | 示例 |
|------|-----------|------|
| QQ | QQ号 | `2946204414` |
| Telegram | Telegram用户ID | `123456789` |
| 其他 | 平台用户唯一标识 | - |

### 配置示例

```json
{
  "owner_id": "2946204414",
  "admin_ids": ["123456789", "987654321"],
  "show_builtin_plugins": false
}
```

## 内置插件说明

以下为 KiraAI 的内置核心插件，默认不在列表中显示：

| 插件名称 | 插件ID | 说明 |
|----------|--------|------|
| builtin | `kira_builtin_plugin` | 核心插件，处理消息元数据 |
| Message Debounce | `kira_debounce_plugin` | 消息防抖，合并短时间内的消息 |
| Session Tools | `kira_session_plugin` | 会话工具，支持跨会话交互 |
| Simple Memory | `kira_plugin_simple_memory` | 简单记忆实现 |
| Tavily Search | `search` | 网络搜索工具 |
| File | `file` | 文件系统访问工具 |

内置插件无法通过此工具启停，以保护系统稳定性。

## Tool 说明

此插件向 AI 提供以下工具：

### list_plugins

列出所有已安装的插件，返回插件名称、ID 和当前状态。

**权限**: 所有人可用

### enable_plugin

启用指定的用户插件。支持插件ID或插件名称，支持模糊匹配。

**权限**: 仅管理员可用

**参数**:
- `plugin_name`: 要启用的插件名称或ID

### disable_plugin

禁用指定的用户插件。支持插件ID或插件名称，支持模糊匹配。

**权限**: 仅管理员可用

**参数**:
- `plugin_name`: 要禁用的插件名称或ID

### get_plugin_info

获取指定插件的详细信息，包括名称、ID、类型、状态、版本、作者和描述。

**权限**: 所有人可用

**参数**:
- `plugin_name`: 要查询的插件名称或ID

## 模糊匹配规则

插件名称匹配支持以下优先级：

1. 精确匹配 plugin_id
2. 精确匹配 display_name
3. 模糊匹配（plugin_id 或 display_name 包含输入字符串）

示例：
- "天气" → 匹配 "天气查询" [weather]
- "weather" → 匹配 [weather]
- "系统" → 匹配 "系统信息插件" [system_info_plugin]

## 设计动机

1. **便捷管理**: 用户可以在聊天界面直接管理插件，无需打开 WebUI
2. **AI 感知**: 让 AI 知道有哪些插件可用，增强上下文理解
3. **多平台支持**: 支持 QQ、Telegram 等多平台统一的权限管理

## 故障排除

### 插件无法加载

1. 检查文件结构是否完整
2. 检查配置文件格式是否正确
3. 查看日志文件获取详细错误信息

### 权限验证失败

1. 确认 `owner_id` 或 `admin_ids` 配置正确
2. 确认用户ID格式正确（字符串格式）
3. 检查日志中的权限验证信息

### 插件列表为空

1. 确认 `data/plugins` 目录下有其他插件
2. 确认其他插件已正确安装
3. 检查 `show_builtin_plugins` 配置
