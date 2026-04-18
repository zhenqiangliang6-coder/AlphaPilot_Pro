# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 状态管理模块
负责持仓状态、策略状态的持久化管理

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import json
import os
import datetime
from config import settings
# 注意：这里只导入函数，不要在这里调用 get_logger()
from utils.logger import get_logger
from core.trader_engine import TraderEngine

class StateManager:
    def __init__(self, engine: TraderEngine):
        self.engine = engine
        self.elite_list = {}

    def load_elite_list(self):
        # 每次调用前先获取 logger 实例，确保不为 None
        logger = get_logger()
        
        if not os.path.exists(settings.STATE_FILE):
            self.elite_list = {}
            if logger: logger.log("[初始化] 未找到状态文件，初始化为空")
            return
        
        try:
            with open(settings.STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.elite_list = data.get('positions', {})
            if logger: logger.log("[初始化] 加载精英名单：" + str(len(self.elite_list)) + "只")
        except Exception as e:
            if logger: logger.log("[警告] 加载状态文件失败：" + str(e))
            self.elite_list = {}

    def save_elite_list(self):
        # 每次调用前先获取 logger 实例
        logger = get_logger()

        if not self.engine.connected:
            if logger: logger.log("[状态] 引擎未连接，跳过保存")
            return

        positions = self.engine.query_positions()
        new_list = {}
        
        if positions:
            codes = [p.stock_code for p in positions if p.volume > 0]
            ticks = self.engine.get_tick_data(codes)
            
            count = 0
            for p in positions:
                if p.volume <= 0: 
                    continue
                code = p.stock_code
                cost = getattr(p, 'open_price', 0.0)
                price = ticks.get(code, {}).get('lastPrice', cost) if ticks else cost
                
                if price <= 0: 
                    price = cost
                
                if cost > 0 and price > 0:
                    profit = (price - cost) / cost
                    if profit > settings.ELITE_PROFIT_THRESHOLD:
                        new_list[code] = {
                            'volume': p.volume,
                            'profit_ratio': round(profit, 4),
                            'close_price': price,
                            'cost_price': cost
                        }
                        count += 1
            
            self.elite_list = new_list
            if logger: logger.log("[保存] 扫描完成，" + str(count) + "只入选精英名单")

        # 强制写入（原子操作）
        temp_file = settings.STATE_FILE + ".tmp"
        data = {
            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'positions': self.elite_list,
            'strategy': 'ELITE_V8'
        }
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子替换：先删除旧文件，再重命名新文件
            if os.path.exists(settings.STATE_FILE):
                os.remove(settings.STATE_FILE)
            os.rename(temp_file, settings.STATE_FILE)
            if logger: logger.log("[保存] 文件写入成功：" + str(settings.STATE_FILE))
        except Exception as e:
            if logger: logger.log("[错误] 保存文件失败：" + str(e))