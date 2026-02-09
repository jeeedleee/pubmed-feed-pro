# macOS 打包方案指南

本文档介绍如何为 macOS 用户打包 PubMed Papers Feed 应用。

---

## ⚠️ 重要前提

**PyInstaller 不支持跨平台打包**：
- ❌ 在 Windows 上无法打包 macOS 应用
- ❌ 在 Linux 上无法打包 macOS 应用
- ✅ 必须在 macOS 系统上执行打包

---

## 方案一：GitHub Actions 自动打包（⭐ 强烈推荐）

使用 GitHub 提供的免费 macOS 运行器自动打包，支持同时构建 Intel 和 Apple Silicon 版本。

### 配置步骤

1. **代码推送到 GitHub 仓库**

2. **创建工作流文件**（已完成）
   - 文件：`.github/workflows/build-macos.yml`

3. **触发自动构建**
   ```bash
   # 方法 A：推送标签自动触发
   git tag v1.0.0
   git push origin v1.0.0
   
   # 方法 B：手动触发
   # 访问 GitHub 仓库页面 → Actions → Build macOS App → Run workflow
   ```

4. **下载构建产物**
   - 构建完成后，在 Actions 页面下载 artifacts
   - 或在 Releases 页面下载（如果是标签触发）

### 输出文件

- `PubMedPapersFeed-macOS-x86_64.zip` - Intel Mac 版本
- `PubMedPapersFeed-macOS-arm64.zip` - Apple Silicon 版本 (M1/M2/M3)

---

## 方案二：本地 macOS 打包

如果你有 Mac 电脑，可以直接在本地打包。

### 步骤

```bash
# 1. 克隆/下载源码
cd pubmed_papers_feed

# 2. 安装依赖
pip install pyinstaller
pip install -r requirements.txt

# 3. 执行打包脚本
chmod +x build_macos.sh
./build_macos.sh
```

### 为不同架构打包

```bash
# Intel Mac (x86_64)
TARGET_ARCH=x86_64 ./build_macos.sh

# Apple Silicon (arm64)
TARGET_ARCH=arm64 ./build_macos.sh

# 通用二进制（Universal Binary）- 体积较大，但兼容两种架构
# 需要分别构建后使用 lipo 合并
```

---

## 方案三：提供源码安装（最简单）

如果不需要打包成可执行文件，可以让 macOS 用户直接安装 Python 环境运行。

### 给用户的安装说明

```bash
# 1. 安装 Python 3.11+（如果未安装）
# 访问 https://www.python.org/downloads/mac-osx/

# 2. 下载项目源码并解压
cd pubmed_papers_feed

# 3. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 复制配置
cp config.yaml.example config.yaml
# 编辑 config.yaml 填写 API key

# 6. 启动应用
python main.py
```

---

## 📦 分发方式对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| GitHub Actions | 免费、自动化、支持双架构 | 需要配置 GitHub 仓库 | ⭐ 推荐大部分情况 |
| 本地打包 | 简单直接、无需网络 | 需要 Mac 电脑 | 个人使用或小范围分发 |
| 源码安装 | 最灵活、可修改代码 | 需要用户安装 Python | 技术用户或开发者 |

---

## 🔐 macOS 安全说明

### 签名与公证

默认打包的应用 **未经过 Apple 签名**，用户首次运行时会看到安全警告。

**解决方法**：
1. 右键点击 `start.command` → 选择 "打开"
2. 前往 **系统设置 > 隐私与安全性** → 点击 **仍要打开**

### 如需正式分发建议

如果要无警告地运行，需要：
1. 加入 Apple Developer Program（$99/年）
2. 使用开发者证书签名应用
3. 提交 Apple 公证（Notarization）

对于个人/小范围分发，目前的方案已足够使用。

---

## 📋 打包文件清单

分发 macOS 版本时，ZIP 中应包含：

```
PubMedPapersFeed-macOS/
├── PubMedPapersFeed      # 主程序（可执行文件）
├── start.command         # 启动脚本
├── config.yaml.example   # 配置模板
├── README.md            # 说明文档
└── macOS使用说明.txt     # macOS 专用说明（中文）
```

---

## 🚀 快速分发流程

### 使用 GitHub Actions（推荐）

```bash
# 1. 确保代码已提交

git add .
git commit -m "Prepare for release"

# 2. 创建版本标签
git tag v1.0.0

# 3. 推送标签触发构建
git push origin v1.0.0

# 4. 等待构建完成，在 GitHub Releases 页面发布
```

### 本地打包分发

```bash
# 1. 在 Mac 上执行打包
./build_macos.sh

# 2. 压缩分发文件
cd dist
zip -r PubMedPapersFeed-macOS.zip PubMedPapersFeed start.command config.yaml.example README.md

# 3. 上传网盘或发送给用户
```

---

## ❓ 常见问题

**Q: Windows 用户能为 Mac 用户打包吗？**  
A: 不能。必须在 macOS 系统上打包。建议使用 GitHub Actions。

**Q: 一个包能同时支持 Intel 和 M1 Mac 吗？**  
A: 可以构建 Universal Binary，但体积会翻倍。建议分开打包。

**Q: 打包后的应用为什么很大？**  
A: PyInstaller 会打包 Python 解释器和所有依赖，通常 50-150MB 是正常的。

**Q: macOS 提示 "无法验证开发者" 怎么办？**  
A: 这是正常的。用户需要前往 **系统设置 > 隐私与安全性** 允许运行。

---

## 📚 相关文件

- `build_macos.sh` - macOS 打包脚本
- `.github/workflows/build-macos.yml` - GitHub Actions 工作流
- `macOS使用说明.txt` - 给用户的使用说明
