"""
股票数据服务 - 使用腾讯财经 API 直接获取数据
"""
import pandas as pd
import json
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
import httpx

# 创建 HTTP 客户端
_http_client: httpx.AsyncClient | httpx.Client | None = None


def _get_client() -> httpx.Client:
    """获取或创建 HTTP 客户端"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://finance.qq.com/',
                'Accept': '*/*',
            }
        )
    return _http_client


# 简单的内存缓存
_cache: dict = {}


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry is None:
        return None
    data, timestamp, ttl = entry
    if datetime.now().timestamp() - timestamp < ttl:
        return data
    if key in _cache:
        del _cache[key]
    return None


def _cache_set(key: str, data, ttl: int = 60):
    _cache[key] = (data, datetime.now().timestamp(), ttl)


def normalize_stock_code(code: str) -> tuple[str, str]:
    """规范化股票代码，返回 (market_code, exchange)
       sz=深圳, sh=上海
    """
    code = code.strip().zfill(6)
    if code.startswith(('00', '30', '002', '003')):
        return code, "sz"
    elif code.startswith(('60', '68', '500', '501')):
        return code, "sh"
    elif code.startswith('8') or code.startswith('4'):
        return code, "bj"
    return code, "sz"


def _get_qq_market_code(code: str) -> str:
    """获取腾讯API的市场前缀"""
    code = code.strip().zfill(6)
    if code.startswith(('00', '30', '002', '003')):
        return "sz"  # 深圳
    elif code.startswith(('60', '68', '500', '501')):
        return "sh"  # 上海
    elif code.startswith('8') or code.startswith('4'):
        return "bj"  # 北交所
    return "sz"


def get_realtime_quote(codes: list[str]) -> pd.DataFrame:
    """获取实时行情"""
    if not codes:
        return pd.DataFrame()

    cache_key = f"realtime:{','.join(sorted(codes))}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        # 构建腾讯行情请求
        qq_codes = []
        for code in codes:
            sym, _ = normalize_stock_code(code)
            mkt = _get_qq_market_code(code)
            qq_codes.append(f"{mkt}{sym}")

        url = f"https://qt.gtimg.cn/q={','.join(qq_codes)}"
        client = _get_client()
        resp = client.get(url)
        text = resp.text

        records = []
        lines = text.strip().split('\n')
        for i, line in enumerate(lines):
            if not line or '=' not in line:
                continue
            # 解析: v_sz000001="51~平安银行~..."
            match = re.search(r'v_\w+="(.+)"', line)
            if not match:
                continue
            data = match.group(1).split('~')
            if len(data) < 50:
                continue
            try:
                stock_code = codes[i] if i < len(codes) else data[2]
                records.append({
                    "代码": data[2] if len(data) > 2 else stock_code,
                    "名称": data[1] if len(data) > 1 else "",
                    "最新价": float(data[3]) if data[3] else 0,
                    "涨跌幅": float(data[32]) if data[32] else 0,
                    "成交量": float(data[6]) if data[6] else 0,
                    "成交额": float(data[37]) if data[37] else 0,
                    "今开": float(data[4]) if data[4] else 0,
                    "最高": float(data[33]) if data[33] else 0,
                    "最低": float(data[34]) if data[34] else 0,
                    "昨收": float(data[5]) if data[5] else 0,
                })
            except (ValueError, IndexError):
                continue

        df = pd.DataFrame(records)
        _cache_set(cache_key, df, ttl=15)
        return df
    except Exception as e:
        print(f"实时行情获取失败: {e}")
        return pd.DataFrame()


def get_kline_hist(
    code: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> pd.DataFrame:
    """
    获取历史K线数据
    period: daily/weekly/monthly/5/15/30/60 分钟
    adjust: qfq=前复权 hfq=后复权 None=不复权
    """
    cache_key = f"kline:{code}:{period}:{start_date}:{end_date}:{adjust}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    sym, _ = normalize_stock_code(code)
    mkt = _get_qq_market_code(code)

    # 分钟数据使用新浪API
    minute_periods = ["5", "15", "30", "60"]
    if period in minute_periods:
        df = _get_minute_data_sina(sym, mkt, period, adjust)
        if not df.empty:
            _cache_set(cache_key, df, ttl=60)  # 分钟数据缓存60秒
        return df

    # 日/周/月数据使用腾讯API
    period_map = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month",
    }
    period_qq = period_map.get(period, "day")

    # 复权处理
    if adjust == "qfq":
        adjust_suffix = "qfq"
    elif adjust == "hfq":
        adjust_suffix = "hfq"
    else:
        adjust_suffix = ""

    # 默认获取500条数据
    limit = 500

    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_{period_qq}{adjust_suffix}&param={mkt}{sym},{period_qq},,,{limit},{adjust_suffix}"
        client = _get_client()
        resp = client.get(url)
        text = resp.text

        # 解析返回数据: kline_dayqfq={...}
        json_match = re.search(r'=({.+})', text)
        if not json_match:
            return pd.DataFrame()

        data = json.loads(json_match.group(1))
        key = f"{mkt}{sym}"

        if key not in data.get("data", {}):
            return pd.DataFrame()

        # 获取数据 - 注意腾讯API返回的key格式可能是 "qfqweek" 而不是 "weekqfq"
        data_key = f"{period_qq}{adjust_suffix}" if adjust_suffix else period_qq
        klines = data["data"][key].get(data_key, [])

        if not klines:
            # 尝试其他可能的key格式
            for k in [f"qfq{period_qq}", f"{period_qq}qfq", period_qq, "day", "qfqday", "hfqday", "dayhfq"]:
                if k in data["data"][key]:
                    klines = data["data"][key][k]
                    break

        if not klines:
            return pd.DataFrame()

        records = []
        for kl in klines:
            if len(kl) >= 6:
                try:
                    records.append({
                        "date": kl[0],
                        "open": float(kl[1]),
                        "close": float(kl[2]),
                        "high": float(kl[3]),
                        "low": float(kl[4]),
                        "volume": float(kl[5]),
                    })
                except (ValueError, IndexError):
                    continue

        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            _cache_set(cache_key, df, ttl=300 if period == "daily" else 3600)
        return df
    except Exception as e:
        print(f"K线获取失败 {code} {period}: {e}")
        return pd.DataFrame()


def get_index_quote(index_code: str = "000001") -> dict:
    """获取指数实时行情"""
    cache_key = f"index:{index_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        index_map = {
            "000001": "sh000001",
            "399001": "sz399001",
            "399006": "sz399006",
            "000688": "sh000688"
        }
        qq_code = index_map.get(index_code, f"sh{index_code}")

        url = f"https://qt.gtimg.cn/q={qq_code}"
        client = _get_client()
        resp = client.get(url)
        text = resp.text

        match = re.search(r'v_\w+="(.+)"', text)
        if match:
            data = match.group(1).split('~')
            if len(data) > 30:
                result = {
                    "代码": data[2] if len(data) > 2 else index_code,
                    "名称": data[1] if len(data) > 1 else "",
                    "最新价": float(data[3]) if data[3] else 0,
                    "涨跌幅": float(data[32]) if data[32] else 0,
                }
                _cache_set(cache_key, result, ttl=15)
                return result
        return {}
    except Exception as e:
        print(f"指数行情获取失败: {e}")
        return {}


def _parse_sina_suggest(text: str) -> list[dict]:
    """
    解析新浪搜索响应
    两种格式：
      名称搜索: "徐工机械,11,000425,sz000425,徐工机械,..."
      代码搜索: "sz000425,11,000425,sz000425,徐工机械,..."
    """
    if not text.startswith('var suggestvalue='):
        return []
    content = text[len('var suggestvalue='):].strip().strip('"').rstrip(';')
    if not content or content == 'N':
        return []

    records = []
    for entry in content.split(';'):
        items = entry.split(',')
        if len(items) < 5:
            continue

        first_field = items[0]
        # 判断格式：市场代码搜索（以sz/sh开头）还是名称搜索
        if first_field.startswith(('sz', 'sh')):
            # 代码搜索格式: 市场代码,类型,代码,市场代码,名称,...
            market_code = items[0]
            code = items[2]
            name = items[4]
        else:
            # 名称搜索格式: 名称,类型,代码,市场代码,名称,...
            name = items[0]
            code = items[2]
            market_code = items[3]

        # 只保留A股
        if (market_code.startswith('sh') or market_code.startswith('sz')) and not name.isdigit():
            records.append({"code": code, "name": name})

    return records


def search_stocks(keyword: str) -> pd.DataFrame:
    """搜索股票 - 使用新浪搜索API"""
    cache_key = f"search:{keyword}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        # 始终使用 UTF-8 URL encode（两种搜索都有效）
        keyword_encoded = urllib.parse.quote(keyword)
        url = f"https://suggest3.sinajs.cn/suggest/type=11,12,13,14,15&key={keyword_encoded}"
        client = _get_client()
        resp = client.get(url)
        text = resp.content.decode('gbk', errors='replace').strip()

        records = _parse_sina_suggest(text)

        # 去重并限制数量
        seen: set[str] = set()
        unique = []
        for r in records:
            if r['code'] not in seen:
                seen.add(r['code'])
                unique.append(r)

        df = pd.DataFrame(unique[:20])
        _cache_set(cache_key, df, ttl=3600)
        return df
    except Exception as e:
        print(f"股票搜索失败: {e}")
        return pd.DataFrame()


def get_daily_hot_stocks(limit: int = 20) -> list:
    """当日个股人气榜（东方财富），返回含代码、名称、排名等；缓存为空时直接获取实时数据。"""
    limit = max(1, min(int(limit), 50))
    cache_key = f"hot:daily:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # 缓存为空时，直接获取实时热门股票数据
    return _fetch_and_cache_hot(limit)


def _fetch_and_cache_hot(limit: int = 20) -> list:
    """从新浪财经人气榜（关注度）获取真实数据；失败时返回空列表。"""
    limit = max(1, min(int(limit), 50))
    cache_key = f"hot:daily:{limit}"

    # 新浪人气榜（按关注度/讨论量排序）
    url = (
        f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
        f"/Market_Center.getHQNodeDataSimple"
        f"?node=hs_a&num={limit}&sort=focus&asc=0&page=1"
    )
    try:
        client = _get_client()
        resp = client.get(url)
        text = resp.content.decode("gbk", errors="replace")
        data = json.loads(text)

        if not isinstance(data, list):
            print(f"新浪人气榜返回格式异常: {text[:200]}")
            _cache_set(cache_key, [], ttl=60)
            return []

        stocks = []
        for idx, item in enumerate(data, start=1):
            symbol = str(item.get("symbol", "")).strip()
            # 去掉 sh/sz/bj 前缀，转6位代码
            for p in ("sh", "sz", "bj", "SH", "SZ", "BJ"):
                if symbol.startswith(p):
                    code = symbol[len(p):].zfill(6)
                    break
            else:
                code = symbol.zfill(6) if symbol.isdigit() else symbol

            try:
                chg = float(item.get("changepercent", 0))
            except (TypeError, ValueError):
                chg = 0.0
            try:
                vol = int(float(item.get("volume", 0) or 0))
            except (TypeError, ValueError):
                vol = 0

            stocks.append({
                "rank": idx,
                "code": code,
                "name": str(item.get("name", "") or "").strip(),
                "change_pct": round(chg, 2),
                "volume": vol,
            })

        _cache_set(cache_key, stocks, ttl=300)
        print(f"新浪人气榜获取成功，共 {len(stocks)} 条")
        return stocks

    except Exception as e:
        print(f"新浪人气榜获取失败: {e}")
        _cache_set(cache_key, [], ttl=60)
        return []


def warm_hot_cache():
    """后台线程预热热门股票缓存（5 分钟刷新一次）。"""
    import threading, time
    def _loop():
        while True:
            _fetch_and_cache_hot(20)
            time.sleep(300)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    print("热门股票后台预热线程已启动")


def get_stock_info(code: str) -> dict:
    """获取股票基本信息"""
    cache_key = f"info:{code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    sym, _ = normalize_stock_code(code)
    mkt = _get_qq_market_code(code)

    try:
        url = f"https://qt.gtimg.cn/q={mkt}{sym}"
        client = _get_client()
        resp = client.get(url)
        text = resp.text

        match = re.search(r'v_\w+="(.+)"', text)
        if match:
            data = match.group(1).split('~')
            if len(data) > 45:
                info = {
                    "代码": data[2] if len(data) > 2 else sym,
                    "名称": data[1] if len(data) > 1 else "",
                    "现价": float(data[3]) if data[3] else 0,
                    "涨跌幅": float(data[32]) if data[32] else 0,
                    "涨跌额": float(data[31]) if data[31] else 0,
                    "成交量": float(data[6]) if data[6] else 0,
                    "成交额": float(data[37]) if data[37] else 0,
                    "振幅": float(data[43]) if len(data) > 43 and data[43] else 0,
                    "最高": float(data[33]) if data[33] else 0,
                    "最低": float(data[34]) if data[34] else 0,
                    "今开": float(data[4]) if data[4] else 0,
                    "昨收": float(data[5]) if data[5] else 0,
                    "市净率": float(data[46]) if len(data) > 46 and data[46] else 0,
                    "市盈率": float(data[39]) if len(data) > 39 and data[39] else 0,
                }
                _cache_set(cache_key, info, ttl=300)
                return info
        return {}
    except Exception as e:
        print(f"股票信息获取失败: {e}")
        return {}


# ─── 分时数据 ────────────────────────────────────────────────────────────────
def get_minute_data(code: str, period: str = "5") -> pd.DataFrame:
    """获取分钟K线数据"""
    cache_key = f"minute:{code}:{period}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # 分钟数据使用日K接口的分钟数据
    return get_kline_hist(code, period=period, adjust="qfq")


# ─── 新浪分钟数据 ─────────────────────────────────────────────────────────────
def _get_minute_data_sina(code: str, market: str, period: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    使用新浪API获取分钟K线数据
    period: 5, 15, 30, 60 (分钟)
    """
    # 新浪代码格式: sz000001, sh600000
    sina_code = f"{market}{code}"

    # 新浪API参数
    scale_map = {"5": 5, "15": 15, "30": 30, "60": 60}
    scale = scale_map.get(period, 30)

    # 新浪API URL
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale={scale}&ma=no&datalen=500"

    try:
        client = _get_client()
        resp = client.get(url)
        data = resp.json()

        if not data or not isinstance(data, list):
            return pd.DataFrame()

        records = []
        for kl in data:
            try:
                records.append({
                    "date": pd.to_datetime(kl.get("day", "")),
                    "open": float(kl.get("open", 0)),
                    "close": float(kl.get("close", 0)),
                    "high": float(kl.get("high", 0)),
                    "low": float(kl.get("low", 0)),
                    "volume": float(kl.get("volume", 0)),
                })
            except (ValueError, TypeError):
                continue

        df = pd.DataFrame(records)
        return df
    except Exception as e:
        print(f"新浪分钟数据获取失败 {code} {period}: {e}")
        return pd.DataFrame()
