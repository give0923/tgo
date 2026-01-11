# AGENTS.md - TGO Web 项目指南

> 本文档为 AI 代码助手提供项目上下文，帮助理解代码结构、技术栈和开发规范。

## 项目概述

TGO Web 是一个现代化的 **AI 智能客服前端应用**，基于 React 19 构建。

### 核心功能

- **AI Agent 管理** - 多 AI Agent 支持，可配置不同智能体
- **实时聊天** - 基于 WuKongIM 的即时通讯，支持 WebSocket 双向通信
- **知识库管理** - 文档/QA/网站三种知识库类型
- **MCP 工具集成** - 工具商店、自定义工具、OpenAPI Schema 解析
- **多平台接入** - Web、微信公众号、小程序、企业微信等渠道
- **工作流编排** - 基于 ReactFlow 的可视化工作流编辑器

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 19.x |
| 语言 | TypeScript | 5.9.x |
| 构建工具 | Vite | 7.x |
| 状态管理 | Zustand | 5.x |
| 样式 | Tailwind CSS | 4.x |
| 路由 | React Router | 7.x |
| 国际化 | i18next | 25.x |
| IM 通讯 | WuKongIM SDK (easyjssdk) | 1.x |
| Markdown | marked + highlight.js | - |
| 图标 | Lucide React + React Icons | - |
| 工作流画布 | ReactFlow | 11.x |

---

## 项目结构

```
src/
├── components/          # UI 组件（按功能域划分）
│   ├── ai/             # AI Agent、工具管理组件
│   ├── chat/           # 聊天功能组件（消息、输入、列表等）
│   ├── knowledge/      # 知识库管理组件
│   ├── layout/         # 布局组件（Sidebar, Layout, ChatWindow）
│   ├── platforms/      # 平台/渠道管理组件
│   ├── settings/       # 设置页组件
│   ├── ui/             # 基础 UI 组件（Button, Modal, Toast等）
│   ├── visitor/        # 访客管理组件
│   └── workflow/       # 工作流编辑器组件
├── hooks/              # 自定义 Hooks
├── pages/              # 页面级组件
├── services/           # API 服务层
├── stores/             # Zustand 状态管理
├── types/              # TypeScript 类型定义
├── utils/              # 工具函数
├── i18n/               # 国际化配置和语言包
├── constants/          # 常量定义
├── data/               # Mock 数据（仅开发用）
└── router/             # 路由配置
```

### 关键目录说明

#### `services/` - API 服务层

所有 HTTP 请求通过 `apiClient` 单例处理：

```typescript
// src/services/api.ts - 核心 API 客户端
import apiClient from '@/services/api';

// 使用示例
await apiClient.get<T>('/endpoint');
await apiClient.post<T>('/endpoint', data);
await apiClient.stream('/endpoint', data, { onMessage, onClose, onError });
```

API 服务按功能模块划分：
- `aiAgentsApi.ts` - AI Agent CRUD
- `conversationsApi.ts` - 会话管理
- `knowledgeBaseApi.ts` - 知识库操作
- `platformsApi.ts` - 平台配置
- `workflowApi.ts` - 工作流管理
- `wukongimApi.ts` / `wukongimWebSocket.ts` - IM 通讯

#### `stores/` - 状态管理

使用 Zustand 进行状态管理，每个功能域有独立的 store：

```typescript
// 使用示例
import { useAuthStore } from '@/stores/authStore';
import { useChatStore } from '@/stores/chatStore';

const { isAuthenticated, login, logout } = useAuthStore();
const { chats, activeChat, setActiveChat } = useChatStore();
```

主要 stores：
- `authStore` - 认证状态
- `chatStore` - 聊天会话
- `messageStore` - 消息管理
- `channelStore` - 频道信息
- `aiStore` - AI Agent 状态
- `platformStore` - 平台配置
- `workflowStore` - 工作流状态

#### `types/` - 类型定义

核心类型定义在 `src/types/index.ts`，包括：
- `Platform`, `PlatformConfig` - 平台/渠道类型
- `Agent`, `AgentResponse` - AI Agent 类型
- `Chat`, `Message`, `MessagePayload` - 聊天消息类型
- `KnowledgeBase`, `KnowledgeFile` - 知识库类型
- `Visitor`, `ChannelInfo` - 访客和频道类型
- `WuKongIM*` - IM 相关类型

---

## 代码规范

### TypeScript 配置

- **严格模式**：启用 `strict: true`
- **无未使用变量**：`noUnusedLocals: true`, `noUnusedParameters: true`
- **显式返回类型**：`noImplicitReturns: true`

### 路径别名

```typescript
// 使用 @ 别名导入
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';
import type { Message } from '@/types';
```

配置映射：
- `@/*` → `src/*`
- `@/components/*` → `src/components/*`
- `@/utils/*` → `src/utils/*`

### ESLint 规则

关键规则：

```javascript
// 禁止直接导入 mock 数据
'no-restricted-imports': ['error', {
  patterns: [{
    group: ['**/data/mock*'],
    message: 'Use mockDataHelper utility instead for production safety.'
  }]
}]

// 生产安全
'no-console': ['warn', { allow: ['warn', 'error'] }]
'no-debugger': 'error'

// 代码质量
'prefer-const': 'error'
'no-var': 'error'
```

### 未使用变量处理

以下划线 `_` 开头的变量名被忽略：

```typescript
// ✅ 正确
const [_unused, setUsed] = useState();
function handler(_event: MouseEvent) { }

// ❌ 错误
const [unused, setUsed] = useState(); // ESLint error
```

---

## 开发指南

### 常用命令

```bash
# 开发
yarn dev              # 启动开发服务器

# 构建
yarn build            # 生产构建 (tsc + vite build)
yarn build:check      # 完整检查 (type-check + lint + build + verify)

# 代码质量
yarn lint             # ESLint 检查
yarn lint:fix         # ESLint 自动修复
yarn type-check       # TypeScript 类型检查
```

### 组件开发模式

#### 功能组件结构

```typescript
import React from 'react';
import { useTranslation } from 'react-i18next';
import { SomeIcon } from 'lucide-react';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
  const { t } = useTranslation();
  
  return (
    <div className="p-4 bg-white rounded-2xl shadow-sm">
      <h2 className="font-bold text-gray-900">{title}</h2>
      <button 
        onClick={onAction}
        className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
      >
        {t('common.action')}
      </button>
    </div>
  );
};

export default MyComponent;
```

#### 状态管理模式

```typescript
// 创建 store
import { create } from 'zustand';

interface MyStore {
  items: Item[];
  loading: boolean;
  fetchItems: () => Promise<void>;
  addItem: (item: Item) => void;
}

export const useMyStore = create<MyStore>((set) => ({
  items: [],
  loading: false,
  
  fetchItems: async () => {
    set({ loading: true });
    try {
      const data = await apiClient.get<Item[]>('/items');
      set({ items: data, loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },
  
  addItem: (item) => set((state) => ({ 
    items: [...state.items, item] 
  })),
}));
```

### API 调用模式

```typescript
import apiClient, { APIError } from '@/services/api';

// GET 请求
const data = await apiClient.get<ResponseType>('/v1/endpoint');

// POST 请求
const result = await apiClient.post<ResponseType>('/v1/endpoint', payload);

// 流式请求 (SSE)
await apiClient.stream('/v1/ai/chat', payload, {
  onMessage: (event, data) => {
    // 处理流式数据
  },
  onClose: () => {
    // 流结束
  },
  onError: (error) => {
    // 错误处理
  },
  signal: abortController.signal,
});

// 错误处理
try {
  await apiClient.post('/v1/action', data);
} catch (error) {
  if (error instanceof APIError) {
    const message = error.getUserMessage();
    const code = error.getErrorCode();
    // 显示用户友好的错误信息
  }
}
```

### 国际化处理

```typescript
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  
  return (
    <div>
      {/* 基础翻译 */}
      <p>{t('common.save')}</p>
      
      {/* 带参数翻译 */}
      <p>{t('chat.messageCount', { count: 5 })}</p>
      
      {/* 带默认值 */}
      <p>{t('new.key', '默认文本')}</p>
    </div>
  );
};
```

语言文件位置：`src/i18n/locales/zh.json`, `src/i18n/locales/en.json`

---

## 设计规范

> 详细规范参见 `docs/DESIGN_GUIDE.md`

### 风格定位

**现代简约 SaaS 风格 + 科技未来感**

关键词：呼吸感、通透、圆润、层级

### 色彩系统

| 用途 | 浅色模式 | 暗黑模式 |
|------|----------|----------|
| 主背景 | `#f8fafc` (slate-50) | `gray-950` |
| 内容容器 | `white` | `gray-900` |
| Primary (AI) | `blue-600` (#2563eb) | - |
| Secondary (工作流) | `purple-600` (#9333ea) | - |
| Accent (工具) | `indigo-600` (#4f46e5) | - |

### 圆角规范

- 小元素（按钮、输入框）：`rounded-xl` (0.75rem)
- 标准卡片：`rounded-2xl` (1rem)
- 大型容器/Modal：`rounded-3xl` (1.5rem)

### 交互动画

```css
/* 基础过渡 */
transition-all duration-300

/* 卡片悬停 */
hover:-translate-y-1 hover:shadow-xl

/* 进入动画 */
animate-in fade-in slide-in-from-bottom-4
```

---

## 关键约定

### 文件命名

- 组件文件：`PascalCase.tsx` (如 `ChatMessage.tsx`)
- 工具函数：`camelCase.ts` (如 `messageFormatting.ts`)
- 类型文件：`camelCase.ts` 或 `index.ts`
- 常量文件：`camelCase.ts` (如 `chat.ts`)

### 组件导出

```typescript
// 默认导出用于页面和主组件
export default MyComponent;

// 命名导出用于工具函数和类型
export { helperFunction, MyType };
```

### 消息类型处理

消息 payload 类型定义在 `MessagePayloadType` 枚举：

```typescript
enum MessagePayloadType {
  TEXT = 1,
  IMAGE = 2,
  FILE = 3,
  RICH_TEXT = 12,
  STREAM = 100,
  // 系统消息：1000-2000
  SYSTEM_STAFF_ASSIGNED = 1000,
  SYSTEM_SESSION_CLOSED = 1001,
  SESSION_TRANSFERRED = 1002,
  MEMORY_CLEARED = 1003,
}
```

### 错误边界

组件应处理加载和错误状态：

```typescript
const MyComponent = () => {
  const { data, loading, error } = useFetch();
  
  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  
  return <Content data={data} />;
};
```

---

## 环境配置

### 运行时配置

API 地址通过以下优先级获取：

1. `window.ENV.VITE_API_BASE_URL` (Docker 运行时注入)
2. `import.meta.env.VITE_API_BASE_URL` (构建时环境变量)
3. `/api` (默认值)

### Docker 部署

```bash
# 构建镜像
docker build -t tgo-web .

# 运行（传入 API 地址）
docker run -p 80:80 -e VITE_API_BASE_URL=http://api.example.com tgo-web
```

---

## 常见任务

### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `src/router/index.tsx` 添加路由
3. 如需国际化，在 `src/i18n/locales/` 添加翻译

### 添加新 API 服务

1. 在 `src/services/` 创建 API 文件
2. 定义请求/响应类型
3. 使用 `apiClient` 发起请求

### 添加新 Store

1. 在 `src/stores/` 创建 store 文件
2. 定义 state 接口和 actions
3. 在组件中使用 hook

### 添加新组件

1. 确定组件所属功能域
2. 在对应的 `src/components/{domain}/` 目录创建
3. 遵循组件开发模式和设计规范

---

## 调试技巧

### 控制台日志

项目中保留的 `console.log` 主要用于：
- 主题切换调试 `[Theme]`
- API URL 输出

生产环境应使用 `console.warn` 和 `console.error`。

### 类型检查

```bash
# 快速类型检查
yarn type-check

# 开发时实时检查（vite-plugin-checker）
yarn dev  # 自动启用
```

### Mock 数据

开发时可使用 `src/utils/mockDataHelper.ts` 安全地访问 mock 数据：

```typescript
import { getMockData } from '@/utils/mockDataHelper';

// 仅在开发环境生效
const mockAgents = getMockData('agents');
```

---

*最后更新: 2026-01-11*
