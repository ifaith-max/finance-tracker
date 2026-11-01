# 记账工具（Streamlit）

一个本地网页记账工具，记录个人收入与支出。数据保存在本地 SQLite 文件里，无需联网。

## 功能
- 添加账目：类型（收入/支出）、金额、分类、日期、备注
- 账目列表：按月/分类筛选，表格展示
- 修改账目：下拉选择一条记录后编辑
- 删除账目：输入 ID 删除
- 分类统计：柱状图 + 统计表（可切换收入/支出）

## 技术栈
- Python 3.12
- Streamlit（网页界面）
- sqlite3（标准库，本地数据库）
- pandas（随 streamlit 自动安装，用于表格/图表）

## 目录结构
- `config.py` — 常量：分类列表、数据库文件名
- `database.py` — 数据层：建表、增删改查、统计（所有 SQL 都在这里）
- `app.py` — 界面层：Streamlit 页面，只负责展示与调用 `database.py`
- `requirements.txt` — 依赖清单
- `finance.db` — SQLite 数据库（首次运行自动生成，不入库）

依赖方向（单向）：`app.py` → `database.py` → `config.py`

## 运行
```bash
pip install -r requirements.txt      # 或 python -m pip install streamlit
python -m streamlit run app.py
```

## 数据库
表 `transactions`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| type | TEXT | `income` / `expense` |
| amount | REAL | 金额，正数 |
| category | TEXT | 分类 |
| date | TEXT | `YYYY-MM-DD` |
| note | TEXT | 备注 |

## 修改分类
改 `config.py` 里的两个常量即可，表单下拉和统计会自动读取：
- `EXPENSE_CATEGORIES`（支出）
- `INCOME_CATEGORIES`（收入）
