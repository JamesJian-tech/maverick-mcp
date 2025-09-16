"""
S&P 500趋势评分系统 - 适配MaverickMCP版本

基于5个技术指标计算综合趋势分数：MA、MACD、ADX、RSI、OBV
- 移动平均线 (MA): 评分范围 (-3, 3)
- MACD: 评分范围 (-2, 2)  
- ADX: 评分范围 (-2, 2)
- RSI: 评分范围 (-1, 1)
- OBV: 评分范围 (-1, 1)

总评分范围: -9到+9，标准化为0-100分
"""

import json
import logging
import os
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import requests
import ta
from pydantic import BaseModel, Field

from maverick_mcp.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
warnings.filterwarnings('ignore')


class TrendScoreInput(BaseModel):
    """趋势评分输入参数"""
    ticker: str = Field(description="股票代码")
    period: str = Field(default="6mo", description="数据期间: 1mo, 3mo, 6mo, 1y, 2y")
    fixed_end_date: Optional[str] = Field(default=None, description="固定截止日期 YYYY-MM-DD")


class BatchTrendScoreInput(BaseModel):
    """批量趋势评分输入参数"""
    tickers: List[str] = Field(description="股票代码列表")
    period: str = Field(default="6mo", description="数据期间")
    fixed_end_date: Optional[str] = Field(default=None, description="固定截止日期 YYYY-MM-DD")


class TrendScoreResult(BaseModel):
    """趋势评分结果"""
    ticker: str
    latest_date: str
    normalized_trend_score: float = Field(description="标准化趋势分数 (0-100)")
    weighted_raw_score: float = Field(description="加权原始分数")
    ma_score: int = Field(description="移动平均线评分")
    macd_score: int = Field(description="MACD评分")
    adx_score: int = Field(description="ADX评分")
    rsi_score: int = Field(description="RSI评分")
    obv_score: int = Field(description="OBV评分")


class SP500TrendScorer:
    """
    S&P 500趋势评分系统
    基于5个技术指标计算综合趋势分数：MA、MACD、ADX、RSI、OBV
    """
    
    def __init__(self, fixed_end_date: Optional[str] = None):
        """
        初始化趋势评分器
        
        Args:
            fixed_end_date: 固定数据截止日期，形如 "YYYY-MM-DD"，不传则用当前日期
        """
        self.fixed_end_date = fixed_end_date
        
        # 根据Excel文件分析得出的权重系统
        # 每个指标的权重 = 2.1 / 9 ≈ 0.2333 (统一权重)
        self.weight = 2.1 / 9
        
        # 技术指标评分范围
        self.score_ranges = {
            'MA': (-3, 3),      # 移动平均线评分范围
            'MACD': (-2, 2),    # MACD评分范围  
            'ADX': (-2, 2),     # ADX评分范围
            'RSI': (-1, 1),     # RSI评分范围
            'OBV': (-1, 1)      # OBV评分范围
        }
    
    def _period_to_days(self, period: str) -> int:
        """将 period 字符串转为天数，仅支持常用取值"""
        mapping = {
            "1mo": 31, "3mo": 93, "6mo": 186,
            "1y": 365, "2y": 730
        }
        return mapping.get(period, 186)  # 默认6mo
    
    def _normalize_polygon_ticker(self, ticker: str) -> str:
        """将常见带'-'的代码转换为 Polygon 格式（如 BRK-B -> BRK.B）"""
        return ticker.replace("-", ".")

    def _latest_trading_date(self, ticker: str = "SPY") -> str:
        """通过 Polygon prev 接口获取最新交易日(UTC)日期字符串 YYYY-MM-DD"""
        api_key = os.environ.get("POLYGON_API_KEY")
        if not api_key:
            # 无密钥时回退为当前日期
            return datetime.utcnow().strftime("%Y-%m-%d")
        try:
            tk = self._normalize_polygon_ticker(ticker)
            url = f"https://api.polygon.io/v2/aggs/ticker/{tk}/prev"
            params = {"adjusted": "true", "apiKey": api_key}
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            js = r.json()
            ts = js.get("results", [{}])[0].get("t")
            if ts:
                return datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"获取最新交易日失败: {e}")
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    def get_stock_data(self, ticker: str, period: str = '6mo') -> Optional[pd.DataFrame]:
        """使用 Polygon API 获取股票数据"""
        api_key = os.environ.get("POLYGON_API_KEY")
        if not api_key:
            logger.error("缺少 POLYGON_API_KEY 环境变量")
            return None
        try:
            days = self._period_to_days(period)
            # 若未设置 fixed_end_date，则使用最新交易日
            if self.fixed_end_date:
                end = datetime.strptime(self.fixed_end_date, "%Y-%m-%d")
            else:
                # 用待查询标的的最新交易日，若失败再回退 SPY
                latest_str = self._latest_trading_date(ticker) or self._latest_trading_date("SPY")
                end = datetime.strptime(latest_str, "%Y-%m-%d")
            start = end - timedelta(days=days)
            tk = self._normalize_polygon_ticker(ticker)
            url = f"https://api.polygon.io/v2/aggs/ticker/{tk}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
            params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": api_key}
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            js = r.json()
            results = js.get("results", [])
            if not results:
                logger.warning(f"Polygon 无数据: {ticker} {start.date()}~{end.date()} -> {js.get('status')}")
                return None
            df = pd.DataFrame(results)
            df["date"] = pd.to_datetime(df["t"], unit="ms")
            df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}, inplace=True)
            df.set_index("date", inplace=True)
            df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
            return df
        except Exception as e:
            logger.error(f"获取 {ticker} 数据失败: {e}")
            return None
    
    def calculate_ma_score(self, data: pd.DataFrame, short_period: int = 20, long_period: int = 50) -> int:
        """计算移动平均线评分"""
        if len(data) < long_period:
            return 0
            
        short_ma = data['Close'].rolling(window=short_period).mean()
        long_ma = data['Close'].rolling(window=long_period).mean()
        
        latest_short = short_ma.iloc[-1]
        latest_long = long_ma.iloc[-1]
        latest_price = data['Close'].iloc[-1]
        
        # 评分逻辑
        if latest_price > latest_short > latest_long:
            if (latest_short - latest_long) / latest_long > 0.05:  # 强烈看涨
                return 3
            elif (latest_short - latest_long) / latest_long > 0.02:  # 中等看涨
                return 2
            else:  # 轻微看涨
                return 1
        elif latest_price > latest_short:
            return 1
        elif latest_price < latest_short < latest_long:
            if (latest_long - latest_short) / latest_long > 0.05:  # 强烈看跌
                return -3
            elif (latest_long - latest_short) / latest_long > 0.02:  # 中等看跌
                return -2
            else:  # 轻微看跌
                return -1
        elif latest_price < latest_short:
            return -1
        else:
            return 0
    
    def calculate_macd_score(self, data: pd.DataFrame) -> int:
        """计算MACD评分"""
        if len(data) < 34:  # MACD需要足够的数据点
            return 0
            
        try:
            # 使用ta库计算MACD
            macd_line = ta.trend.MACD(data['Close']).macd()
            macd_signal = ta.trend.MACD(data['Close']).macd_signal()
            
            if macd_line.isna().iloc[-1] or macd_signal.isna().iloc[-1]:
                return 0
            
            latest_macd = macd_line.iloc[-1]
            latest_signal = macd_signal.iloc[-1]
            prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else latest_macd
            prev_signal = macd_signal.iloc[-2] if len(macd_signal) > 1 else latest_signal
            
            # 评分逻辑
            if latest_macd > latest_signal:
                if latest_macd > 0 and (latest_macd - prev_macd) > 0:  # 强烈看涨
                    return 2
                else:  # 轻微看涨
                    return 1
            elif latest_macd < latest_signal:
                if latest_macd < 0 and (latest_macd - prev_macd) < 0:  # 强烈看跌
                    return -2
                else:  # 轻微看跌
                    return -1
            else:
                return 0
        except Exception as e:
            logger.error(f"MACD计算失败: {e}")
            return 0
    
    def calculate_adx_score(self, data: pd.DataFrame, period: int = 14) -> int:
        """计算ADX评分"""
        if len(data) < period + 14:
            return 0
            
        try:
            # 使用ta库计算ADX相关指标
            adx_indicator = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close'], window=period)
            adx = adx_indicator.adx()
            plus_di = adx_indicator.adx_pos()
            minus_di = adx_indicator.adx_neg()
            
            if adx.isna().iloc[-1] or plus_di.isna().iloc[-1] or minus_di.isna().iloc[-1]:
                return 0
            
            latest_adx = adx.iloc[-1]
            latest_plus_di = plus_di.iloc[-1]
            latest_minus_di = minus_di.iloc[-1]
            
            # 评分逻辑
            if latest_adx > 30:  # 强趋势
                if latest_plus_di > latest_minus_di:
                    return 2  # 强烈看涨
                else:
                    return -2  # 强烈看跌
            elif latest_adx > 20:  # 中等趋势
                if latest_plus_di > latest_minus_di:
                    return 1  # 轻微看涨
                else:
                    return -1  # 轻微看跌
            else:  # 弱趋势
                return 0
        except Exception as e:
            logger.error(f"ADX计算失败: {e}")
            return 0
    
    def calculate_rsi_score(self, data: pd.DataFrame, period: int = 14) -> int:
        """计算RSI评分"""
        if len(data) < period:
            return 0
            
        try:
            # 使用ta库计算RSI
            rsi = ta.momentum.RSIIndicator(data['Close'], window=period).rsi()
            
            if rsi.isna().iloc[-1]:
                return 0
            
            latest_rsi = rsi.iloc[-1]
            
            # 评分逻辑
            if latest_rsi > 70:  # 超买
                return -1
            elif latest_rsi > 60:  # 看涨
                return 1
            elif latest_rsi < 30:  # 超卖
                return 1
            elif latest_rsi < 40:  # 看跌
                return -1
            else:  # 中性
                return 0
        except Exception as e:
            logger.error(f"RSI计算失败: {e}")
            return 0
    
    def calculate_obv_score(self, data: pd.DataFrame) -> int:
        """计算OBV评分"""
        if len(data) < 10:
            return 0
            
        try:
            # 使用ta库计算OBV
            obv = ta.volume.OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume()
            
            if len(obv) < 5:
                return 0
            
            # 计算OBV趋势
            recent_obv = obv.iloc[-5:].values
            obv_trend = np.polyfit(range(len(recent_obv)), recent_obv, 1)[0]
            
            # 评分逻辑
            if obv_trend > 0:
                return 1  # 成交量支持上涨
            elif obv_trend < 0:
                return -1  # 成交量支持下跌
            else:
                return 0
        except Exception as e:
            logger.error(f"OBV计算失败: {e}")
            return 0
    
    def calculate_trend_score(self, ticker: str, period: str = '6mo') -> Optional[TrendScoreResult]:
        """计算单个股票的趋势评分"""
        data = self.get_stock_data(ticker, period)
        if data is None or len(data) < 50:
            logger.warning(f"数据不足，无法计算 {ticker} 的趋势评分")
            return None
        
        # 计算各技术指标评分
        ma_score = self.calculate_ma_score(data)
        macd_score = self.calculate_macd_score(data)
        adx_score = self.calculate_adx_score(data)
        rsi_score = self.calculate_rsi_score(data)
        obv_score = self.calculate_obv_score(data)
        
        # 计算加权原始分数
        weighted_raw_score = (ma_score + macd_score + adx_score + rsi_score + obv_score) * self.weight
        
        # 标准化分数 (0-100)
        normalized_score = (weighted_raw_score + 2.1) / 4.2 * 100
        normalized_score = max(0, min(100, normalized_score))  # 确保在0-100范围内
        
        return TrendScoreResult(
            ticker=ticker,
            latest_date=data.index[-1].strftime('%Y-%m-%d'),
            normalized_trend_score=round(normalized_score, 2),
            weighted_raw_score=round(weighted_raw_score, 3),
            ma_score=ma_score,
            macd_score=macd_score,
            adx_score=adx_score,
            rsi_score=rsi_score,
            obv_score=obv_score
        )
    
    def calculate_batch_scores(
        self, 
        tickers: List[str], 
        period: str = '6mo'
    ) -> List[TrendScoreResult]:
        """批量计算股票的趋势评分"""
        results = []
        total = len(tickers)
        
        for i, ticker in enumerate(tickers):
            logger.info(f"处理进度: {i+1}/{total} - {ticker}")
            
            score_data = self.calculate_trend_score(ticker, period)
            if score_data:
                results.append(score_data)
        
        # 按标准化分数排序
        results.sort(key=lambda x: x.normalized_trend_score, reverse=True)
        
        return results


# 创建全局实例
trend_scorer = SP500TrendScorer()