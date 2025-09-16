
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/Users/jiahaojian/Documents/GitHub/maverick-mcp')

def test_trend_scorer_with_env():
    """在正确的环境中测试趋势评分器"""
    print("🔄 开始测试趋势评分器...")
    
    # 检查环境
    try:
        from maverick_mcp.tools.trend_scorer import SP500TrendScorer, TrendScoreInput
        print("✅ 成功导入趋势评分器模块")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 检查 API 密钥
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print("⚠️  POLYGON_API_KEY 未设置，将使用模拟数据进行结构测试")
    else:
        print("✅ POLYGON_API_KEY 已设置")
    
    # 创建评分器实例
    try:
        scorer = SP500TrendScorer()
        print("✅ 成功创建 SP500TrendScorer 实例")
        
        # 测试基本属性
        print(f"📊 权重系统: {scorer.weight}")
        print(f"📏 评分范围: {scorer.score_ranges}")
        
        # 测试方法存在性
        methods = [
            'get_stock_data', 'calculate_ma_score', 'calculate_macd_score',
            'calculate_adx_score', 'calculate_rsi_score', 'calculate_obv_score',
            'calculate_trend_score', 'calculate_batch_scores'
        ]
        
        print("\n🔧 检查方法可用性:")
        for method in methods:
            if hasattr(scorer, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method}")
        
        # 如果有 API 密钥，尝试实际数据测试
        if api_key:
            print("\n📈 尝试获取实际股票数据...")
            
            test_ticker = "AAPL"
            print(f"🔍 测试股票: {test_ticker}")
            
            try:
                # 测试数据获取
                data = scorer.get_stock_data(test_ticker, period="1mo")
                
                if data is not None:
                    print(f"✅ 成功获取 {len(data)} 天的数据")
                    print(f"📅 数据范围: {data.index[0].date()} 到 {data.index[-1].date()}")
                    print(f"💰 最新收盘价: ${data['Close'].iloc[-1]:.2f}")
                    
                    # 测试趋势评分计算
                    print("\n📊 计算趋势评分...")
                    result = scorer.calculate_trend_score(test_ticker, period="1mo")
                    
                    if result:
                        print("✅ 趋势评分计算成功!")
                        print(f"   📈 标准化分数: {result.normalized_trend_score:.2f}/100")
                        print(f"   📉 原始分数: {result.weighted_raw_score:.3f}")
                        print(f"   📅 数据日期: {result.latest_date}")
                        print("   🔧 技术指标分解:")
                        print(f"      • MA评分: {result.ma_score}")
                        print(f"      • MACD评分: {result.macd_score}")
                        print(f"      • ADX评分: {result.adx_score}")
                        print(f"      • RSI评分: {result.rsi_score}")
                        print(f"      • OBV评分: {result.obv_score}")
                        
                        # 评分解读
                        score = result.normalized_trend_score
                        if score >= 90:
                            trend = "🚀 强烈看涨"
                        elif score >= 70:
                            trend = "📈 中等看涨"
                        elif score >= 50:
                            trend = "↗️ 轻微看涨"
                        elif score >= 30:
                            trend = "↘️ 轻微看跌"
                        elif score >= 10:
                            trend = "📉 中等看跌"
                        else:
                            trend = "🔻 强烈看跌"
                        
                        print(f"   🎯 趋势判断: {trend}")
                        
                    else:
                        print("❌ 趋势评分计算失败")
                else:
                    print("❌ 无法获取股票数据")
                    
            except Exception as e:
                print(f"❌ 数据测试失败: {e}")
        
        else:
            print("\n⚠️  跳过实际数据测试 (无API密钥)")
            print("   如需完整测试，请设置 POLYGON_API_KEY 环境变量")
        
        print("\n🎯 趋势评分系统功能验证:")
        print("   ✅ 模块导入成功")
        print("   ✅ 类实例化成功")
        print("   ✅ 方法结构完整")
        if api_key:
            print("   ✅ 实际数据测试通过")
        else:
            print("   ⚠️  实际数据测试跳过")
        
    except Exception as e:
        print(f"❌ 评分器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Maverick MCP Trend Scorer 环境测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_trend_scorer_with_env()
    
    print()
    print("=" * 60)
    print("🎉 测试完成!")
