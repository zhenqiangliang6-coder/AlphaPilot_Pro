《AlphaPilot_Pro 推送到 GitHub 技术指南》预览版（最终版由任务自动生成）
1. 初始化 Git 仓库
bash
git init
2. 添加所有文件
bash
git add .
3. 提交文件
bash
git commit -m "初始化：提交 AlphaPilot_Pro 项目"
4. 绑定远程仓库（SSH）
bash
git remote add origin git@github.com:zhenqiangliang6-coder/AlphaPilot_Pro.git
5. 切换默认分支为 main
bash
git branch -M main
6. 推送到 GitHub
bash
git push -u origin main
7. 常见错误与解决方案
Permission denied → SSH key 属于另一个账号

remote origin already exists → 删除后重新添加

冲突 → 拉取远程后再推送