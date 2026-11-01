"""界面层：Streamlit 页面，负责展示与交互，调用 database.py 的函数。"""

from datetime import date

import pandas as pd
import streamlit as st

import database as db
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES


st.set_page_config(page_title="记账工具", page_icon="💰", layout="wide")

# 首次运行时建表（表已存在则跳过）
db.init_db()

# 操作后的提示（添加/修改/删除成功后显示）
flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

st.title("💰 记账工具")


def type_label(t):
    """数据库里的 'income'/'expense' 转成中文。"""
    return "收入" if t == "income" else "支出"


def amount_display(r):
    """金额显示：收入 +，支出 -。"""
    sign = "+" if r["type"] == "income" else "-"
    return f"{sign}{r['amount']:.2f}"


def record_label(r):
    """编辑下拉里每条记录的显示文字。"""
    return f"#{r['id']} | {r['date']} | {r['category']} | {amount_display(r)} | {r['note']}"


# ---------- 侧边栏：筛选 ----------
st.sidebar.header("筛选")

months = db.get_months()
month_filter = st.sidebar.selectbox("月份", ["全部"] + months, key="filter_month")
month = None if month_filter == "全部" else month_filter

all_categories = EXPENSE_CATEGORIES + INCOME_CATEGORIES
category_filter = st.sidebar.selectbox("分类", ["全部"] + all_categories, key="filter_category")
category = None if category_filter == "全部" else category_filter

st.sidebar.caption("月份筛选同时作用于列表和统计；分类筛选仅作用于列表。")


# ---------- 三个页签 ----------
tab_add, tab_list, tab_stats = st.tabs(["添加账目", "账目列表", "分类统计"])


# ===== 页签 1：添加账目 =====
with tab_add:
    st.subheader("添加账目")

    add_type_label = st.radio("类型", ["支出", "收入"], horizontal=True, key="add_type")
    add_type = "expense" if add_type_label == "支出" else "income"

    add_cats = EXPENSE_CATEGORIES if add_type == "expense" else INCOME_CATEGORIES
    add_category = st.selectbox("分类", add_cats, key=f"add_category_{add_type}")

    add_amount = st.number_input(
        "金额（元）", min_value=0.01, step=0.01, format="%.2f", key="add_amount"
    )
    add_date = st.date_input("日期", value=date.today(), key="add_date")
    add_note = st.text_input("备注（可选）", key="add_note")

    if st.button("添加", type="primary"):
        db.add_transaction(
            add_type, add_amount, add_category, add_date.isoformat(), add_note.strip()
        )
        # 清空输入，避免连续记同一笔
        for k in (
            "add_amount", "add_note", "add_date",
            "add_category_expense", "add_category_income",
        ):
            st.session_state.pop(k, None)
        st.session_state["flash"] = "已添加 ✅"
        st.rerun()


# ===== 页签 2：账目列表 =====
with tab_list:
    st.subheader("账目列表")

    records = db.list_transactions(month, category)
    if not records:
        st.info("暂无记录，去「添加账目」页签记一笔吧。")
    else:
        df = pd.DataFrame(
            [
                {
                    "ID": r["id"],
                    "类型": type_label(r["type"]),
                    "金额（元）": amount_display(r),
                    "分类": r["category"],
                    "日期": r["date"],
                    "备注": r["note"],
                }
                for r in records
            ]
        )
        st.dataframe(df, hide_index=True)

    # ----- 修改账目 -----
    st.divider()
    st.subheader("修改账目")

    all_records = db.list_transactions()  # 全部记录，不套筛选
    if not all_records:
        st.info("暂无记录可修改。")
    else:
        id_to_label = {r["id"]: record_label(r) for r in all_records}
        selected_id = st.selectbox(
            "选择要修改的记录",
            [r["id"] for r in all_records],
            format_func=lambda i: id_to_label[i],
            key="edit_select",
        )
        selected = db.get_transaction(selected_id)

        edit_type_label = st.radio(
            "类型", ["支出", "收入"], horizontal=True,
            index=0 if selected["type"] == "expense" else 1,
            key=f"edit_type_{selected_id}",
        )
        edit_type = "expense" if edit_type_label == "支出" else "income"

        edit_cats = EXPENSE_CATEGORIES if edit_type == "expense" else INCOME_CATEGORIES
        edit_category = st.selectbox(
            "分类", edit_cats,
            index=edit_cats.index(selected["category"]) if selected["category"] in edit_cats else 0,
            key=f"edit_category_{selected_id}_{edit_type}",
        )
        edit_amount = st.number_input(
            "金额（元）", min_value=0.01, step=0.01, format="%.2f",
            value=float(selected["amount"]), key=f"edit_amount_{selected_id}",
        )
        edit_date = st.date_input(
            "日期", value=date.fromisoformat(selected["date"]), key=f"edit_date_{selected_id}",
        )
        edit_note = st.text_input("备注", value=selected["note"], key=f"edit_note_{selected_id}")

        if st.button("保存修改", type="primary"):
            db.update_transaction(
                selected_id, edit_type, edit_amount, edit_category,
                edit_date.isoformat(), edit_note.strip(),
            )
            st.session_state["flash"] = f"已保存 #{selected_id} ✅"
            st.rerun()

    # ----- 删除账目 -----
    st.divider()
    st.subheader("删除账目")

    delete_id = st.number_input("输入要删除的账目 ID", min_value=1, step=1, key="delete_id")
    if st.button("删除"):
        if db.get_transaction(delete_id) is None:
            st.warning(f"ID {delete_id} 不存在。")
        else:
            db.delete_transaction(delete_id)
            st.session_state.pop("delete_id", None)
            st.session_state.pop("edit_select", None)
            st.session_state["flash"] = f"已删除 #{delete_id} ✅"
            st.rerun()


# ===== 页签 3：分类统计 =====
with tab_stats:
    st.subheader("分类统计")
    st.caption(f"当前月份筛选：{month_filter}")

    stat_type_label = st.radio("统计类型", ["支出", "收入"], horizontal=True, key="stat_type")
    stat_type = "expense" if stat_type_label == "支出" else "income"

    rows = db.get_stats(month, stat_type)
    if not rows:
        st.info("该条件下暂无数据。")
    else:
        # 柱状图
        chart_df = pd.DataFrame(
            {"分类": [r["category"] for r in rows], "金额（元）": [r["total"] for r in rows]}
        ).set_index("分类")
        st.bar_chart(chart_df)

        # 统计表
        total_count = sum(r["count"] for r in rows)
        total_amount = sum(r["total"] for r in rows)
        table = pd.DataFrame(
            [{"分类": r["category"], "笔数": r["count"], "总金额（元）": round(r["total"], 2)}
             for r in rows]
            + [{"分类": "合计", "笔数": total_count, "总金额（元）": round(total_amount, 2)}]
        )
        st.dataframe(table, hide_index=True)
