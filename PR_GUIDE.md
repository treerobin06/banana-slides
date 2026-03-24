# 提交 PR 指南 - 删除20页限制

## 修改内容
删除了 `backend/services/prompts.py` 中的20页限制规则。

## 提交步骤

### 1. 创建新分支
```bash
git checkout -b remove-20-page-limit
```

### 2. 只提交相关修改（推荐）
如果只想提交删除20页限制的修改：

```bash
# 暂存其他修改
git stash

# 只添加 prompts.py 的修改
git add backend/services/prompts.py

# 提交
git commit -m "feat: 移除PPT页数20页限制

- 删除提示词中的'生成的幻灯片切勿超过20页'限制
- 允许AI根据内容需要生成任意页数的大纲"
```

### 3. 或者提交所有修改
如果想包含所有当前修改（包括风格指令优化等）：

```bash
# 添加所有修改
git add backend/services/prompts.py backend/services/ai_service.py backend/services/task_manager.py backend/controllers/project_controller.py backend/controllers/page_controller.py

# 提交
git commit -m "feat: 移除PPT页数20页限制并优化提示词

- 删除提示词中的20页限制
- 优化AI提示词，增加风格指令和四部分描述结构
- 改进页面描述生成逻辑"
```

### 4. 推送到远程仓库
```bash
git push origin remove-20-page-limit
```

### 5. 在GitHub创建PR
1. 访问：https://github.com/Anionex/banana-slides
2. 点击 "New Pull Request"
3. 选择 `remove-20-page-limit` 分支
4. 填写PR标题和描述：

**标题：**
```
feat: 移除PPT页数20页限制
```

**描述：**
```markdown
## 修改内容
- 删除了 `backend/services/prompts.py` 中"生成的幻灯片切勿超过20页"的限制规则

## 影响
- AI现在可以根据内容需要生成任意页数的大纲
- 不再强制限制PPT页数上限

## 测试建议
- 测试生成超过20页的大纲是否正常工作
- 验证页数计算和封面/封底识别功能
```

## 注意事项
- 确保代码没有语法错误
- 确保修改符合项目规范
- PR描述要清晰说明修改内容和原因



