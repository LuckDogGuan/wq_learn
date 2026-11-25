from Core.constants.global_ops import *

from itertools import product
from collections import defaultdict



def ts_factory(op, field):
    """
    针对给定的时序操作符，在不同回溯时间窗口 (5, 22, 66, 120, 240天) 下生成 Alpha 表达式。
    
    参数:
        op (str): 时序操作符名称（如 ts_rank, ts_delta 等）。
        field (str): 字段名或预处理后的子表达式。
        
    返回:
        list: 生成的时序 Alpha 表达式列表。
    """
    output = []
    days = [5, 22, 66, 120, 240]
    
    for day in days:
        alpha = "%s(%s, %d)"%(op, field, day)
        output.append(alpha)
    
    return output

def ts_comp_factory(op, field, factor, paras):
    """
    带有额外超参数的时序复合操作符生成工厂（如 ts_percentage, ts_decay_exp_window, ts_moment 等）。
    
    参数:
        op (str): 复合时序操作符。
        field (str): 数据字段。
        factor (str): 超参数关键字名称。
        paras (list): 超参数候选取值列表。
        
    返回:
        list: 组合生成的复合 Alpha 表达式列表。
    """
    output = []
    l1, l2 = [5, 22, 66, 240], paras
    comb = list(product(l1, l2))
    
    for day, para in comb:
        if type(para) == float:
            alpha = "%s(%s, %d, %s=%.1f)"%(op, field, day, factor, para)
        elif type(para) == int:
            alpha = "%s(%s, %d, %s=%d)"%(op, field, day, factor, para)
            
        output.append(alpha)
    
    return output

def vector_factory(op, field):
    """
    向量结合截面数据（如市值 cap）的操作符生成工厂。
    
    参数:
        op (str): 向量操作符。
        field (str): 字段。
        
    返回:
        list: 生成的 Vector Alpha 表达式列表。
    """
    output = []
    vectors = ["cap"]
    
    for vector in vectors:
        alpha = "%s(%s, %s)"%(op, field, vector)
        output.append(alpha)
    
    return output

def twin_field_factory(op, field, fields):
    """
    双字段交互操作符生成工厂（如字段间的相关性、协方差计算等）。
    
    参数:
        op (str): 双字段操作符。
        field (str): 主字段。
        fields (list): 候选对照字段列表。
        
    返回:
        list: 交互组合生成的 Alpha 表达式列表。
    """
    output = []
    days = [5, 22, 66, 240]
    outset = list(set(fields) - set([field]))
    
    for day in days:
        for counterpart in outset:
            alpha = "%s(%s, %s, %d)"%(op, field, counterpart, day)
            output.append(alpha)
    
    return output

def first_order_factory(fields, ops_set):
    """
    一阶 Alpha 表达式生成主工厂。对给定的数据字段集合套用 ops_set 中的各种单字段算子。
    
    参数:
        fields (list): 基础字段或预处理表达式列表。
        ops_set (list): 允许使用的操作符列表。
        
    返回:
        list: 一阶 Alpha 表达式汇总列表。
    """
    alpha_set = []
    for field in fields:
        # 原样字段直接作为候选
        alpha_set.append(field)

        for op in ops_set:
            if op == "ts_percentage":
                alpha_set += ts_comp_factory(op, field, "percentage", [0.5])

            elif op == "ts_decay_exp_window":
                alpha_set += ts_comp_factory(op, field, "factor", [0.5])

            elif op == "ts_moment":
                alpha_set += ts_comp_factory(op, field, "k", [2, 3, 4])

            elif op == "ts_entropy":
                alpha_set += ts_comp_factory(op, field, "buckets", [10])

            elif op.startswith("ts_") or op == "inst_tvr":
                alpha_set += ts_factory(op, field)

            elif op.startswith("vector"):
                alpha_set += vector_factory(op, field)

            elif op == "signed_power":
                alpha = "%s(%s, 2)"%(op, field)
                alpha_set.append(alpha)

            else:
                alpha = "%s(%s)"%(op, field)
                alpha_set.append(alpha)

    return alpha_set

def group_factory(op, field, region):
    """
    横截面分组操作符生成工厂（如 group_rank, group_zscore），支持细分行业、市值、流动性与行业交互等多重分组。
    
    参数:
        op (str): 分组操作符（如 group_rank, group_zscore, group_vector 等）。
        field (str): 输入因子表达式。
        region (str): 交易地区（如 USA, GLB）。
        
    返回:
        list: 分组扩展后的 Alpha 表达式列表。
    """
    output = []
    vectors = ["cap"] 
    
    usa_group_13 = ['pv13_h_min2_3000_sector','pv13_r2_min20_3000_sector','pv13_r2_min2_3000_sector',
                    'pv13_r2_min2_3000_sector', 'pv13_h_min2_focused_pureplay_3000_sector']
    
    # 构造基于分位数的桶（Bucket）分组条件
    cap_group = "bucket(rank(cap), range='0.1, 1, 0.1')"
    asset_group = "bucket(rank(assets),range='0.1, 1, 0.1')"
    sector_cap_group = "bucket(group_rank(cap, sector),range='0.1, 1, 0.1')"
    sector_asset_group = "bucket(group_rank(assets, sector),range='0.1, 1, 0.1')"

    vol_group = "bucket(rank(ts_std_dev(returns,20)),range = '0.1, 1, 0.1')"
    liquidity_group = "bucket(rank(close*volume),range = '0.1, 1, 0.1')"

    groups = ["market", "sector", "industry", "subindustry",
              cap_group, asset_group, sector_cap_group, sector_asset_group, vol_group, liquidity_group]
    
    groups += usa_group_13
        
    for group in groups:
        if op.startswith("group_vector"):
            for vector in vectors:
                alpha = "%s(%s,%s,densify(%s))"%(op, field, vector, group)
                output.append(alpha)
        elif op.startswith("group_percentage"):
            alpha = "%s(%s,densify(%s),percentage=0.5)"%(op, field, group)
            output.append(alpha)
        else:
            alpha = "%s(%s,densify(%s))"%(op, field, group)
            output.append(alpha)
        
    return output

def get_group_second_order_factory(first_order, group_ops, region):
    """
    二阶分组 Alpha 生成工厂，在一阶 Alpha 基础上叠加 group_ 截面操作符。
    
    参数:
        first_order (list): 一阶 Alpha 表达式列表。
        group_ops (list): 分组操作符列表。
        region (str): 交易地区。
        
    返回:
        list: 二阶 Alpha 表达式汇总列表。
    """
    second_order = []
    for fo in first_order:
        for group_op in group_ops:
            second_order += group_factory(group_op, fo, region)
    return second_order

def trade_when_factory(op, field, region):
    """
    条件交易触发因子工厂 (`trade_when`)，结合开启条件 (open_events) 与退出条件 (exit_events) 构造因子。
    
    参数:
        op (str): 条件交易算子（如 trade_when）。
        field (str): 基础信号字段。
        region (str): 交易地区。
        
    返回:
        list: trade_when 条件因子表达式列表。
    """
    output = []
    open_events = [
        "ts_arg_max(volume, 5) == 0", "ts_corr(close, volume, 20) < 0",
        "ts_corr(close, volume, 5) < 0", "ts_mean(volume,10)>ts_mean(volume,60)",
        "group_rank(ts_std_dev(returns,60), sector) > 0.7", "ts_zscore(returns,60) > 2",
        "ts_arg_min(volume, 5) > 3",
        "ts_std_dev(returns, 5) > ts_std_dev(returns, 20)",
        "ts_arg_max(close, 5) == 0", "ts_arg_max(close, 20) == 0",
        "ts_corr(close, volume, 5) > 0", "ts_corr(close, volume, 5) > 0.3", "ts_corr(close, volume, 5) > 0.5",
        "ts_corr(close, volume, 20) > 0", "ts_corr(close, volume, 20) > 0.3", "ts_corr(close, volume, 20) > 0.5",
        "ts_regression(returns, %s, 5, lag = 0, rettype = 2) > 0"%field,
        "ts_regression(returns, %s, 20, lag = 0, rettype = 2) > 0"%field,
        "ts_regression(returns, ts_step(20), 20, lag = 0, rettype = 2) > 0",
        "ts_regression(returns, ts_step(5), 5, lag = 0, rettype = 2) > 0"
    ]

    exit_events = ["abs(returns) > 0.1", "-1"]

    for oe in open_events:
        for ee in exit_events:
            alpha = "%s(%s, %s, %s)"%(op, oe, field, ee)
            output.append(alpha)
    return output