import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'quick-start',
      label: '快速开始',
    },
    {
      type: 'doc',
      id: 'install-and-config',
      label: '安装与配置',
    },
    {
      type: 'doc',
      id: 'domain-and-ssl',
      label: '域名与 SSL 配置',
    },
  ],
};

export default sidebars;