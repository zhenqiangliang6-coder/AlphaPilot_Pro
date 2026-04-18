# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 邮件信号接收器（专业版）
从邮箱自动接收并解析交易信号

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import imaplib
import email
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime
from html import unescape

# ================= 【配置区域】 =================
EMAIL_USER = "497720537@qq.com"
EMAIL_PASS = "zzdqngmxfudubgea"  # ⚠️ 请确保这是授权码
IMAP_SERVER = "imap.qq.com"

# 路径配置
SIGNAL_DIR = r"C:\Users\Administrator\Desktop\ESC\signals"
LOG_DIR = r"C:\Users\Administrator\Desktop\ESC\logs_receiver"
PROCESSED_IDS_FILE = os.path.join(SIGNAL_DIR, ".processed_email_ids.json")

# 策略配置 (可选，若为 None 则完全信任发送端数据，不过滤)
# 建议：发送端已经做过过滤，接收端最好只做格式清洗，不做业务逻辑过滤，防止双重标准
MIN_RATIO_THRESHOLD = None  # 设置为 None 禁用接收端过滤，或填入数值如 0.23

# ================= 【工具函数】 =================

def setup_logging():
    """初始化日志目录"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SIGNAL_DIR, exist_ok=True)
    os.makedirs(os.path.join(SIGNAL_DIR, "processed"), exist_ok=True)
    
    log_file = os.path.join(LOG_DIR, f"receiver_{datetime.now().strftime('%Y%m%d')}.log")
    return log_file

def log_message(msg, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except: pass

def load_processed_ids(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_processed_id(file_path, email_id):
    ids = load_processed_ids(file_path)
    ids.add(email_id)
    # 限制历史记录数量，防止文件过大
    if len(ids) > 1000:
        ids = set(list(ids)[-500:])
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(list(ids), f)

def normalize_stock_code(code_str):
    """
    智能标准化股票代码
    输入: "600000" 或 "600000.SH" 或 "000001.SZ"
    输出: "600000.SH"
    """
    code_str = str(code_str).strip()
    
    # 如果已经包含后缀，直接返回（清理可能的空格）
    if '.SH' in code_str or '.SZ' in code_str or '.BJ' in code_str:
        return code_str.upper()
    
    # 纯数字处理
    if not code_str.isdigit():
        # 尝试提取数字部分
        match = re.search(r'(\d+)', code_str)
        if match:
            code_str = match.group(1)
        else:
            return None
            
    if code_str.startswith(('60', '68', '51', '56')): # 51/56 是 ETF，通常在上交所
        return f"{code_str}.SH"
    elif code_str.startswith(('00', '30', '15')): # 15 是深市 ETF/转债
        return f"{code_str}.SZ"
    elif code_str.startswith(('43', '83', '87')): # 北交所
        return f"{code_str}.BJ"
    else:
        # 未知类型，默认返回 SH 或原样（视情况而定，这里保守返回 None 或 SH）
        log_message(f"⚠️ 未知代码前缀: {code_str}, 默认视为 SH", LOG_FILE)
        return f"{code_str}.SH"

# ================= 【核心解析逻辑】 =================

def parse_html_table(html_content, log_file):
    """解析神经元视图 HTML 表格，具备极强的容错性"""
    soup = BeautifulSoup(html_content, 'lxml') # lxml 解析速度最快
    tables = soup.find_all('table')
    
    if not tables:
        log_message("❌ 未在视图中找到任何表格", log_file)
        return []

    # 假设第一个表格是信号表
    table = tables[0]
    rows = table.find_all('tr')
    
    if len(rows) <= 1:
        return []

    signals = []
    log_message(f"📊 发现表格，共 {len(rows)-1} 行数据", log_file)

    for i, row in enumerate(rows[1:], start=1): # 跳过表头
        cols = row.find_all(['td', 'th']) # 兼容某些不规范表格
        
        # 严格检查列数 (至少需要 代码, 名称, 信号, 价格, 量比)
        if len(cols) < 5:
            continue
        
        try:
            # 获取文本并去除 HTML 实体 (如 &nbsp;)
            raw_code = unescape(cols[0].get_text(strip=True))
            raw_name = unescape(cols[1].get_text(strip=True))
            raw_action = unescape(cols[2].get_text(strip=True))
            raw_price = unescape(cols[3].get_text(strip=True)).replace(',', '')
            raw_ratio = unescape(cols[4].get_text(strip=True)).replace(',', '')
            
            # 数据清洗与转换
            if not raw_code or not raw_price or not raw_ratio:
                raise ValueError("关键字段为空")
                
            price = float(raw_price)
            ratio = float(raw_ratio)
            
            # 🔥 动态过滤 (仅当配置了阈值时生效)
            if MIN_RATIO_THRESHOLD is not None and ratio < MIN_RATIO_THRESHOLD:
                log_message(f"🗑️ [行{i}] 过滤: {raw_code} (量比={ratio} < {MIN_RATIO_THRESHOLD})", log_file)
                continue
            
            # 标准化代码
            full_code = normalize_stock_code(raw_code)
            if not full_code:
                log_message(f"❌ [行{i}] 代码格式无效: {raw_code}", log_file)
                continue
            
            # 动作识别 (支持多种写法)
            action = "HOLD"
            if "买入" in raw_action or "BUY" in raw_action.upper():
                action = "BUY"
            elif "卖出" in raw_action or "SELL" in raw_action.upper():
                action = "SELL"
            
            signal_obj = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "code": full_code,
                "name": raw_name,
                "action": action,
                "price": price,
                "volume_ratio": ratio, # 统一字段名为 volume_ratio 以匹配下单脚本
                "source": "AlphaPilot_Email"
            }
            signals.append(signal_obj)
            log_message(f"✅ [行{i}] 解析成功: {full_code} [{raw_name}] {action} @ {price} (VR:{ratio})", log_file)
            
        except Exception as e:
            log_message(f"⚠️ [行{i}] 解析失败: {str(e)} | 原始数据: {[c.get_text() for c in cols[:3]]}", log_file)
            # 继续处理下一行，不因单行错误中断
            
    return signals

def save_signals_to_txt(signals, log_file):
    if not signals:
        log_message("⚠️ 本次没有有效因子被保存。", log_file)
        return
    
    # 文件名包含时间戳到微秒，防止高并发冲突
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"signal_batch_{timestamp}.txt"
    filepath = os.path.join(SIGNAL_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for sig in signals:
                # ensure_ascii=False 保证中文正常显示
                line = json.dumps(sig, ensure_ascii=False)
                f.write(line + '\n')
        
        log_message(f"💾 成功保存 {len(signals)} 条因子至: {filename}", log_file)
        return True
    except Exception as e:
        log_message(f"❌ 保存文件失败: {e}", log_file)
        return False

# ================= 【主流程】 =================

def fetch_and_process_emails(log_file):
    processed_ids = load_processed_ids(PROCESSED_IDS_FILE)
    mail = None
    
    try:
        log_message("🔌 正在连接 AlphaPilotAi 服务器...", log_file)
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=10)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX")
        
        # 搜索未读邮件
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            log_message("❌ 搜索因子失败", log_file)
            return

        email_ids = messages[0].split()
        if not email_ids:
            # log_message("📬 没有新因子", log_file) # 日志太吵，注释掉
            return

        log_message(f"📬 发现 {len(email_ids)} 新因子", log_file)

        new_count = 0
        for e_id in email_ids:
            eid_str = e_id.decode('utf-8')
            
            # 🔥 防重检查
            if eid_str in processed_ids:
                log_message(f"⏭️ 新因子 {eid_str} 已处理过，跳过", log_file)
                # 即使跳过的也标记为已读，保持邮箱整洁
                mail.store(e_id, '+FLAGS', '\\Seen')
                continue

            res, msg_data = mail.fetch(e_id, "(RFC822)")
            if res != "OK":
                continue
                
            raw_email = msg_data[0][1]
            email_msg = email.message_from_bytes(raw_email)
            subject = email_msg.get('subject', 'No Subject')
            log_message(f"📩 正在解析因子: {subject}", log_file)
            
            html_content = ""
            
            # 提取 HTML 部分
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))
                    
                    if ctype == "text/html" and "attachment" not in cdispo:
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            payload = part.get_payload(decode=True)
                            if payload:
                                html_content = payload.decode(charset, errors='ignore')
                                break
                        except Exception as e:
                            log_message(f"⚠️ 解码 HTML 失败: {e}", log_file)
            else:
                if email_msg.get_content_type() == "text/html":
                    try:
                        charset = email_msg.get_content_charset() or 'utf-8'
                        payload = email_msg.get_payload(decode=True)
                        if payload:
                            html_content = payload.decode(charset, errors='ignore')
                    except: pass
            
            if html_content and "<table" in html_content:
                signals = parse_html_table(html_content, log_file)
                
                if signals:
                    if save_signals_to_txt(signals, log_file):
                        # 只有成功保存后才标记为已读并记录 ID
                        mail.store(e_id, '+FLAGS', '\\Seen')
                        save_processed_id(PROCESSED_IDS_FILE, eid_str)
                        new_count += 1
                        log_message(f"✅  AlphaPilot {eid_str} 处理完成", log_file)
                else:
                    log_message(f"⚠️ AlphaPilotAi  {eid_str} 中未提取到有效信号", log_file)
                    # 即使没信号，也标记为已读，避免死循环
                    mail.store(e_id, '+FLAGS', '\\Seen')
                    save_processed_id(PROCESSED_IDS_FILE, eid_str)
            else:
                log_message(f"⏭️ AlphaPilotAi  {eid_str} 无有效 HTML 表格", log_file)

        if new_count > 0:
            log_message(f"🎉 本轮共成功处理 {new_count} 次有效信号因子", log_file)
            
    except Exception as e:
        log_message(f"❌ 因子处理主循环异常: {e}", log_file)
        time.sleep(30) # 异常后暂停久一点
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except: pass

if __name__ == "__main__":
    LOG_FILE = setup_logging()
    log_message("🚀 AlphaPilot 监听服务 (Pro 版) 启动...", LOG_FILE)
    log_message(f"📂 信号保存目录: {SIGNAL_DIR}", LOG_FILE)
    log_message(f"📝 日志文件: {LOG_FILE}", LOG_FILE)
    
    while True:
        fetch_and_process_emails(LOG_FILE)
        time.sleep(35) # 每 35秒轮询一次