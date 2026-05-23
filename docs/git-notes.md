# Git 课堂笔记

## 核心概念

- **提交（commit）**：一次有说明的版本记录，包含作者、时间和改动内容。
- **暂存区（staging area）**：提交前的准备区域，用于组织本次要提交的改动。
- **远程仓库（remote repository）**：托管在 GitHub 上的仓库副本，用于多人协作。

## 命令速记

```bash
# 查看当前状态
git status

# 查看改动内容
git diff

# 添加到暂存区
git add <文件>

# 提交到本地仓库
git commit -m "提交信息"

# 查看提交历史
git log --oneline

# 推送到远程仓库
git push origin main
```

## 协作模型

```
工作区 → git add → 暂存区 → git commit → 本地仓库 → git push → 远程仓库
```

## 实践记录

> 请在此新增一行，记录你的收获。格式：`- [用户名] 你的收获`

- [demo-speaker] Git 协作的核心是把修改过程交代清楚。
