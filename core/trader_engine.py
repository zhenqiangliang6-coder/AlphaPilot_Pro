# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 交易引擎核心模块
负责与QMT交易终端交互，执行买卖操作

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant, xtdata
from config import settings
from utils.logger import get_logger

# 修复：不在模块加载时获取 logger，而是在每次使用时动态获取
# 这样可以确保 logger 已经初始化

class TraderEngine:
    def __init__(self):
        self.trader = None
        self.account = None
        self.connected = False

    def start(self, session_id):
        # 修复：在方法内部获取 logger，确保此时 logger 已初始化
        log = get_logger()
        
        self.trader = XtQuantTrader(settings.QMT_PATH, session_id)
        self.trader.register_callback(MyCallback())
        self.trader.start()
        
        if self.trader.connect() != 0:
            log.log("[错误] 连接 QMT 失败")
            return False
        
        import time
        time.sleep(2)
        
        self.account = StockAccount(settings.ACCOUNT_ID, "STOCK")
        if self.trader.subscribe(self.account) != 0:
            log.log("[错误] 订阅账户失败")
            return False
            
        self.connected = True
        log.log("[成功] 交易引擎初始化完成")
        return True

    def query_positions(self):
        if not self.connected: return []
        return self.trader.query_stock_positions(self.account) or []

    def query_asset(self):
        if not self.connected: return None
        return self.trader.query_stock_asset(self.account)

    def get_tick_data(self, codes):
        """获取行情数据 - 专家级防假死优化"""
        log = get_logger()  # 动态获取 logger
        if not codes: 
            return {}
        try:
            # 过滤空代码列表
            valid_codes = [c for c in codes if c and isinstance(c, str)]
            if not valid_codes:
                return {}
            
            # 【专家修复】QMT xtdata 在长时间运行后可能断开订阅，导致返回空字典
            # 每次请求前尝试重新订阅（xtdata.subscribe_whole_quote 是幂等的）
            try:
                xtdata.subscribe_whole_quote(valid_codes)
            except:
                pass
            
            tick_data = xtdata.get_full_tick(valid_codes)
            
            # 如果返回空，记录一次警告，方便排查是否是 QMT 服务端问题
            if not tick_data:
                log.log("[警告] QMT 行情接口返回为空，请检查 QMT 客户端是否正常运行")
                
            return tick_data if tick_data else {}
        except Exception as e:
            log.log("[数据] 获取行情失败：" + str(e))
            return {}

    def order_stock(self, code, action, volume, price, strategy_tag):
        """
        action: 'BUY' or 'SELL'
        """
        log = get_logger()  # 动态获取 logger
        if not self.connected:
            log.log("[下单] 引擎未连接，跳过 " + str(code))
            return False
        
        order_type = xtconstant.STOCK_BUY if action == "BUY" else xtconstant.STOCK_SELL
        import time
        order_id = "AUTO_" + str(strategy_tag) + "_" + str(int(time.time()))
        
        try:
            seq = self.trader.order_stock_async(
                self.account, code, order_type, volume,
                xtconstant.FIX_PRICE, price,
                strategy_tag, order_id
            )
            log.log("[成功] 下单：" + str(code) + " " + str(action) + " " + str(volume) + "股 @ " + str(price))
            return True
        except Exception as e:
            log.log("[错误] 下单失败 " + str(code) + ": " + str(e))
            return False

    def run_forever(self):
        if self.trader:
            self.trader.run_forever()

    def stop(self):
        if self.trader:
            self.trader.stop()

class MyCallback(XtQuantTraderCallback):
    def on_connected(self):
        log = get_logger()
        log.log("[系统] QMT 服务连接成功")
    
    def on_disconnected(self):
        log = get_logger()
        log.log("[系统] QMT 服务断开")
    
    def on_stock_trade(self, trade): 
        log.log("[成交] " + str(trade.stock_code) + " " + str(trade.order_type) + " " + str(trade.traded_volume) + "股")
    
    def on_order_error(self, err): 
        log.log("[错误] 委托错误 " + str(err.stock_code) + ": " + str(err.error_msg))
