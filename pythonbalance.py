# coding=utf-8
"""
AlphaPilot Pro - Python T0配平工具（Mini QMT版）

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

# mini python base library
import time

from queue import Queue
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback

from xtquant.xttype import StockAccount
from xtquant.xtdata import get_full_tick, get_instrument_detail
from xtquant import xtconstant

# stragegy library
import sys, re, traceback

if sys.version_info.major != 3:
    sys.exit('版本不受支持，请使用python3.x！')

import os

TRADE = 'trade'
ORDER = 'order'
CANCEL_ERROR = 'cancel_order'
ORDER_ERROR = 'order_error'

PART_CANCEL = 53
CANCELED = 54

import logging
from logging.handlers import RotatingFileHandler

appLogger = logging.getLogger(__name__ + 'python配平')
# 可以设置日志级别
appLogger.setLevel(logging.DEBUG)

# stderr流，控制日志输出到标准显示器
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# file流，控制日志输出到指定路径
handler = RotatingFileHandler(r'..\userdata_mini\log\python balance.log', mode='a', maxBytes=1024*1024*25, backupCount=2)
handler.setLevel(logging.DEBUG)

fmt = logging.Formatter("[%(asctime)s] [%(name)s] [%(module)s] [%(lineno)d] [%(levelname)s] %(message)s")

fmt_stream = logging.Formatter("[%(asctime)s] [%(module)s] %(message)s")

console.setFormatter(fmt_stream)
handler.setFormatter(fmt)

appLogger.addHandler(console)


appLogger.addHandler(handler)


class StrategyMniQmtT0(XtQuantTraderCallback):

    def __init__(self, over_order_price=0.02, trading_time=False, loop=10):
        """

        :param over_order_price:超价设置
        :param loop:轮询周期

        """
        ud_path, ud_session, account, self._strategy_name, stocks, volumes, directions = parse_local_command(0)
        # 库基础配置
        self.acc = account
        self.price_dict = self.full_up_down_price(stocks)
        # qmt 库初始化
        self.t = XtQuantTrader(ud_path, ud_session)
        self.acc = StockAccount(account)
        self.t.register_callback(self)
        self.t.start()
        r1 = self.t.connect()
        self.t.subscribe(self.acc)

        self.tzbz = time.strftime('%Y%m%d %H%M%S')  # 配平默认使用的投资备注
        if r1 != 0:
            raise ValueError('连接client 失败，错误状态:%d' % r1)

        # 参数
        self.over_order_price = over_order_price
        self.loop_time = loop
        # self.stocks = stocks                        # 股票
        # self.volumes = volumes                      # 量
        # self.volumes = volumes                      # 方向

        # 包装目标任务
        self.total_dict_buy = {}
        self.total_dict_sell = {}
        self.total_trade_list = list(set(stocks))

        if len(self.total_trade_list) != len(stocks):
            appLogger.critical('传入的配平股票有重复，请重试！')
            raise ValueError('传入的配平股票有重复，请重试！')

        for i, s in enumerate(stocks):
            if directions[i] == 1:  # 需要卖 配平
                self.total_dict_sell[s] = volumes[i]
            elif directions[i] == 0:  # 需要买 配平
                self.total_dict_buy[s] = volumes[i]
            else:
                appLogger.error('{}未知的买卖类型{}，跳过配平该股票'.format(s, directions[i]))
        # 记录委托状态的字典
        self.ordered_status = Queue()  # 根据股票唯一配平原则（即配平篮子中股票是唯一的，不存在一个股票需要2种配平的情况），key为股票，value为状态
        self.ready_to_buy = self.total_dict_buy.copy()  # 可买股票池
        self.ready_to_sell = self.total_dict_sell.copy()  # 可卖股票池

        self.ordered = {}  # 记录下单股票和数量，以存储下单报错时的下单参数
        self.cancelable_list = [48, 49, 50, 51, 52, 55]
        self.ordered_id = {}  # 记录报单的信息，key stock, value [order_id, buy or sell. ]

        # 变量
        self.__first_call = False
        self.trading_time = trading_time  # 非交易时间是否可继续配平
        # 程序内计时器
        self.__timetag = time.time
        self.__trade_time = self.__timetag()

    def full_up_down_price(self, stocks):
        price_dict={}
        for s in stocks:
            detail = get_instrument_detail(s)
            price_dict[s] = []
            if detail:
                price_dict[s].append(detail['UpStopPrice'])
                price_dict[s].append(detail['DownStopPrice'])
            else:
                appLogger.debug(f"{s}未取到涨跌停信息")
        appLogger.debug(f"股票涨跌停价：{price_dict}")
        return price_dict

    @property
    def __has_ordered(self):
        if not self.__first_call:
            self.__first_call = True
            return False
        else:
            return self.__first_call

    def __call_sleep_before_next_loop(self):
        self.__trade_time += self.loop_time

    def init(self):
        appLogger.info('配平开始'+'=='*30)
        self.__handlebar()

    def __handlebar(self):
        while 1:
            clocker = self.__timetag() >= self.__trade_time  # 定期检查是否有未完成的任务，如果没有则程序退出
            if time.strftime('%H%M%S') > '153002':
                if self.trading_time:
                    appLogger.error('交易时间已过！不再配平')
                    if self.total_dict_buy:
                        appLogger.error('买方向剩余配平任务：{}'.format(self.total_dict_buy))
                    if self.total_dict_sell:
                        appLogger.error('卖方向剩余配平任务：{}'.format(self.total_dict_sell))
                    break
                else:
                    pass
            if self.__has_ordered:
                # r =
                self.update(clocker)
            if not clocker:
                continue
            if self.check_order_status():
                # 可能会做其他工作，如结束任务，退出循环
                appLogger.error('配平任务完成')
                break

            appLogger.info('剩余任务(卖):{}'.format(self.total_dict_sell))
            appLogger.info('剩余任务(买):{}'.format(self.total_dict_buy))
            # 下单
            if len(self.ready_to_buy) + len(self.ready_to_sell) >0:
                appLogger.debug("order")
            else:
                appLogger.debug('empty')
            if self.ready_to_buy:
                appLogger.debug(f'ready_to_buy:{self.ready_to_buy}')
                self.do_trade(self.ready_to_buy, xtconstant.STOCK_BUY)
                appLogger.debug(f"order buy finish")
            if self.ready_to_sell:
                appLogger.debug(f'ready_to_sell:{self.ready_to_sell}')
                self.do_trade(self.ready_to_sell, xtconstant.STOCK_SELL)
                appLogger.debug(f"order sell finish")
            self.__call_sleep_before_next_loop()
        appLogger.info('配平完成，任务结束！')

    def update(self, clocker):
        loop_start = time.time()
        while 1:
            if self.ordered_status.empty():
                break
            if time.time() - loop_start>10:
                break
            trade_info = self.ordered_status.get()
            __type = trade_info[0]
            __obj = trade_info[1]
            stock = __obj.stock_code

            if __type == TRADE:
                if __obj.order_type == xtconstant.STOCK_SELL:
                    if stock in self.total_dict_sell:
                        self.total_dict_sell[stock] -= __obj.traded_volume
                        if self.total_dict_sell[stock] <= 0:  # 单品种任务完成 则从总任务中剔除
                            del self.total_dict_sell[stock]
                else:
                    if stock in self.total_dict_buy:
                        self.total_dict_buy[stock] -= __obj.traded_volume
                        if self.total_dict_buy[stock] <= 0:
                            del self.total_dict_buy[stock]
            elif __type == ORDER:
                if __obj.order_status in [PART_CANCEL, CANCELED]: # 已撤
                    if __obj.order_type == xtconstant.STOCK_BUY and stock not in self.ready_to_buy and stock in self.total_dict_buy:
                        self.ready_to_buy[__obj.stock_code] = min(__obj.order_volume - __obj.traded_volume, self.total_dict_buy[stock])
                    elif __obj.order_type == xtconstant.STOCK_SELL and stock not in self.ready_to_sell and stock in self.total_dict_sell:
                        self.ready_to_sell[__obj.stock_code] = min(__obj.order_volume - __obj.traded_volume, self.total_dict_sell[stock])
                    appLogger.debug('已撤,cancel success order_id:{},stock_code:{},order_volume:{},order_status:{},order_type:{},{}'.format(__obj.order_id, __obj.stock_code, __obj.order_volume, __obj.order_status, __obj.order_type, __obj.traded_volume))
                elif __obj.order_status == 57: # 废单
                    if __obj.order_type == xtconstant.STOCK_BUY and stock not in self.ready_to_buy and stock in self.total_dict_buy:
                        self.ready_to_buy[__obj.stock_code] = min(__obj.order_volume - __obj.traded_volume,self.total_dict_buy[stock])
                    elif __obj.order_type == xtconstant.STOCK_SELL and stock not in self.ready_to_sell and stock in self.total_dict_sell:
                        self.ready_to_sell[__obj.stock_code] = min(__obj.order_volume - __obj.traded_volume,self.total_dict_sell[stock])
                    appLogger.debug('废单,order failed order_id:{},stock_code:{},order_volume:{},order_status:{},order_type:{},{}'.format(__obj.order_id, __obj.stock_code, __obj.order_volume, __obj.order_status, __obj.order_type, __obj.traded_volume))
                else:  # 其他情况
                    appLogger.debug(f"order info:{__obj.order_id},stock_code:{__obj.stock_code},order_volume:{__obj.order_volume},order_status:{__obj.order_status},order_type:{__obj.order_type},{__obj.traded_volume}")
                    continue
            elif __type == CANCEL_ERROR:

                if stock not in self.total_dict_sell and stock not in self.total_dict_buy:
                    continue
                if clocker:
                    _cancel_symbol = self.do_cancel(__obj.order_id)  # 撤单
                    appLogger.debug(f'recancel: {__obj.order_id}, {__obj.stock_code}, {_cancel_symbol}')
                    if _cancel_symbol < 0:  # 报单失败，忽略该委托
                        self.ordered_status.put([CANCEL_ERROR, __obj])
                else:
                    self.ordered_status.put([CANCEL_ERROR, __obj])

    def check_order_status(self):
        if (not self.total_dict_sell) and (not self.total_dict_buy):
            return True
        else:
            # 对非成交委托进行撤单
            for s in self.ordered_id:
                order_id = self.ordered_id[s][0]
                order_type = self.ordered_id[s][1]
                if order_type == xtconstant.STOCK_BUY:
                    if s in self.total_dict_buy and self.total_dict_buy[s] > 0:
                        _cancel_symbol = self.do_cancel(order_id)  # 撤单
                        appLogger.debug(f'cancel: {order_id}, {s}, {_cancel_symbol}')
                        if _cancel_symbol < 0:  # 报单失败，忽略该委托
                            __obj = self.t.query_stock_order(self.acc, order_id)
                            if __obj is not None:
                                self.ordered_status.put([CANCEL_ERROR, __obj])
                            else:
                                appLogger.error(f'query order failed {order_id}')
                elif order_type == xtconstant.STOCK_SELL:
                    if s in self.total_dict_sell and self.total_dict_sell[s] > 0:
                        _cancel_symbol = self.do_cancel(order_id)  # 撤单
                        appLogger.debug(f'cancel: {order_id}, {s}, {_cancel_symbol}')
                        if _cancel_symbol < 0:  # 报单失败，忽略该委托
                            __obj = self.t.query_stock_order(self.acc, order_id)
                            if __obj is not None:
                                self.ordered_status.put([CANCEL_ERROR, __obj])
                            else:
                                appLogger.error(f'query order failed {order_id}')
            self.ordered_id = {}
            return False

    def do_cancel(self, order_id):
        return self.t.cancel_order_stock(self.acc, order_id)

    def do_trade(self, basket, types):
        quoter = list(basket.keys())
        market_data = get_full_tick(quoter)
        if types == xtconstant.STOCK_SELL:  # 卖
            for s in quoter:
                v = basket[s]
                close = market_data[s]['lastPrice']
                order_price = self.price_dict.get(s,{10000,-10000})[-1]
                order_price = round(max(order_price,close - self.over_order_price), 2)
                r = self.passorder(types, self.acc, s, xtconstant.FIX_PRICE, order_price , v,self._strategy_name, self.tzbz)
                if r > 0:
                    orders = type('order', (), {'order_id': r, 'stock_code': s, 'order_volume': v, 'order_status': 49, 'order_type': xtconstant.STOCK_SELL, 'traded_volume': 0, 'order_remark': self.tzbz, 'price': order_price})
                    self.on_stock_order(orders)  # xtquant不推待报状态，这里自己造
                    self.ordered[r] = orders
                    del self.ready_to_sell[s]
                    self.ordered_id[s] = [r, xtconstant.STOCK_SELL]
                else:
                    appLogger.debug(f'order_stock error, {self.acc.account_id}, {s}, {types}, {v}, {xtconstant.FIX_PRICE}, {close - self.over_order_price}, {self._strategy_name}, {self.tzbz}')
        else:
            for s in quoter:  # 买
                v = basket[s]
                close = market_data[s]['lastPrice']
                order_price = self.price_dict.get(s, {10000, -10000})[0]
                order_price = round(min(order_price, close + self.over_order_price), 2)
                r = self.passorder(types, self.acc, s, xtconstant.FIX_PRICE, order_price, v,self._strategy_name, self.tzbz)
                if r > 0:
                    orders = type('order', (), {'order_id': r, 'stock_code': s, 'order_volume': v, 'order_status': 49,'order_type': xtconstant.STOCK_BUY, 'traded_volume': 0, 'order_remark': self.tzbz, 'price': order_price})
                    self.on_stock_order(orders)
                    self.ordered[r] = orders
                    del self.ready_to_buy[s]
                    self.ordered_id[s] = [r, xtconstant.STOCK_BUY]
                else:
                    appLogger.debug(f'order_stock error, {self.acc.account_id}, {s}, {types}, {v}, {xtconstant.FIX_PRICE}, {close + self.over_order_price}, {self._strategy_name}, {self.tzbz}')

    def passorder(self, order_type, acct, stock_code, price_type, price, volume, strategy_name, tzbz):
        return self.t.order_stock(acct, stock_code, order_type, volume, price_type, price, strategy_name, tzbz)

    def on_stock_order(self, order):
        if not order.order_id in self.ordered and order.order_remark !=self.tzbz:
            appLogger.error('order_id：{}不是配平委托，忽略'.format(order.order_id))
            return
        self.ordered_status.put([ORDER, order])
        appLogger.debug(f"recv order:{order.order_id},stock_code:{order.stock_code},order_volume:{order.order_volume},order_status:{order.order_status},order_type:{order.order_type},{order.traded_volume},{order.price}")

    def on_stock_trade(self, trade):
        if not trade.order_id in self.ordered and trade.order_remark !=self.tzbz:
            appLogger.error('order_id：{}不是配平委托，忽略'.format(trade.order_id))
            return
        self.ordered_status.put([TRADE, trade])
        appLogger.debug('已成交：stock_code: {},traded_volume: {},direction：{}'.format(trade.stock_code, trade.traded_volume, trade.order_type))

    def on_cancel_error(self, cancel_error):
        if not cancel_error.order_id in self.ordered:
            appLogger.error('order_id：{}不是配平委托，忽略'.format(cancel_error.order_id))
            return
        appLogger.error('cancel error  error_msg:{},order_id:{}'.format(cancel_error.error_msg, cancel_error.order_id))
        order = self.t.query_stock_order(self.acc, cancel_error.order_id)
        if order is not None:
            self.ordered_status.put([CANCEL_ERROR, order])
        else:
            appLogger.error(f"{cancel_error.order_i}撤单失败")

    def on_order_error(self, order_error):
        if not order_error.order_id in self.ordered and order_error.order_remark != self.tzbz:
            appLogger.error('order_id：{}不是配平委托，忽略'.format(order_error.order_id))
            return
        order = self.t.query_stock_order(self.acc, order_error.order_id)
        if not order:  # 这个似乎是不安全的代替方案，暂时query的结果是空，需要确定问题所在
            order = self.ordered[order_error.order_id]
        if order.order_type == xtconstant.STOCK_BUY and order.stock_code not in self.ready_to_buy and order.stock_code in self.total_dict_buy:
            self.ready_to_buy[order.stock_code] = min(order.order_volume, self.total_dict_buy[order.stock_code])
        elif order.order_type == xtconstant.STOCK_SELL and order.stock_code not in self.ready_to_sell and order.stock_code in self.total_dict_sell:
            self.ready_to_sell[order.stock_code] = min(order.order_volume, self.total_dict_sell[order.stock_code])
        appLogger.error('order_id:{}下单失败 error_msg:{}'.format(order_error.order_id, order_error.error_msg))


def parse_local_command(by_cmd=1):
    if by_cmd == 0:
        # cmd格式 空格分割，股票 数量，方向之间还用英文逗号隔开，并且他们之间一一对应
        # userdata路径 session_id account '000001.SZ,000002.SZ' '100,200' '1,0 ' 1：买  0：卖
        _ud_path, _ud_session, _account, _strategy_name, _stock, _volume, _direction, broker_type = sys.argv[1:]
        _stock = _stock.split(',')
        _volume = [int(v) for v in _volume.split(',')]
        _direction = [int(v) for v in _direction.split(',')]
        _broker_type = int(broker_type)
        # 检查参数完整性：
        if not len(_stock) == len(_volume) == len(_direction):
            raise ValueError('不正确的传参,入参长度：stock：{}下单量：{}方向：{}'.format(len(_stock), len(_volume), len(_direction)))
    else:  # 测试时使用，
        _ud_path = r'E:\qmt\trunk\100001\迅投极速交易终端 睿智融科版\userdata_mini'
        _ud_session = 123456
        _account = '2100000018'
        _stock = ['002235.SZ', '002658.SZ', '600000.SH']
        _volume = [2000, 1000, 200]
        _direction = [0, 0, 1]  # 1卖，0买
        _strategy_name = ''
        _broker_type = 2
    appLogger.debug(f'{_ud_path} {_ud_session} {_account} {_broker_type} {_strategy_name}')
    return _ud_path, int(_ud_session), _account, _strategy_name, _stock, _volume, _direction


if __name__ == "__main__":

    over_order_price = 0.02  # 超价设置
    loop = 5  # 轮询间隔，默认10s,实际实盘可能要更长
    try:
        t = StrategyMniQmtT0(over_order_price, True, loop)
        t.init()
        t.t.stop()
    except:
        msg = traceback.format_exc()
        appLogger.fatal('遇到意外的情况，配平结束')
        appLogger.fatal(msg)
        t.t.stop()
        sys.exit(-1)

