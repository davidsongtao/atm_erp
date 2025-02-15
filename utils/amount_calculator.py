"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：amount_calculator.py.py
@Author   ：King Songtao
@Time     ：2025/2/15 下午5:06
@Contact  ：king.songtao@gmail.com
"""


def calculate_total_amount(income1: float, income2: float, assigned_cleaner: str, conn) -> tuple[float, float]:
    """计算工单总金额

    Args:
        income1: 现金收入
        income2: 转账收入
        assigned_cleaner: 保洁组名称
        conn: 数据库连接

    Returns:
        tuple: (订单金额, 总金额(含GST))
    """
    # 检查保洁组的ABN状态
    if assigned_cleaner and assigned_cleaner != "暂未派单":
        result = conn.query(
            "SELECT has_abn FROM clean_teams WHERE team_name = :team_name",
            params={'team_name': assigned_cleaner},
            ttl=0
        )
        has_abn = bool(result.iloc[0]['has_abn']) if not result.empty else False
    else:
        has_abn = False

    # 计算订单金额（不含GST）
    order_amount = income1 + income2

    # 计算总金额
    # 如果保洁组有ABN，则不计算GST
    total_amount = order_amount if has_abn else income1 + (income2 * 1.1)

    return order_amount, total_amount
