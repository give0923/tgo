
需要配置的 GitHub Secrets：
在你的 GitHub 仓库设置中添加以下 secrets（Settings → Secrets and variables → Actions → New repository secret）：

Docker Hub:
DOCKERHUB_USERNAME - 你的 Docker Hub 用户名
DOCKERHUB_TOKEN - Docker Hub Access Token（在 Docker Hub → Account Settings → Security → New Access Token 创建）

阿里云 ACR:
ALIYUN_REGISTRY_USERNAME - 阿里云容器镜像服务用户名
ALIYUN_REGISTRY_PASSWORD - 阿里云容器镜像服务密码（或访问凭证）
