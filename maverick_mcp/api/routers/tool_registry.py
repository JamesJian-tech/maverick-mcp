"""
Tool registry to register router tools directly on main server.
This avoids Claude Desktop's issue with mounted router tool names.
"""

import logging
from datetime import datetime

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_technical_tools(mcp: FastMCP) -> None:
    """Register technical analysis tools directly on main server"""
    from maverick_mcp.api.routers.technical import (
        get_macd_analysis,
        get_rsi_analysis,
        get_support_resistance,
    )

    # Import enhanced versions with proper timeout handling and logging
    from maverick_mcp.api.routers.technical_enhanced import (
        get_full_technical_analysis_enhanced,
        get_stock_chart_analysis_enhanced,
    )
    from maverick_mcp.validation.technical import TechnicalAnalysisRequest

    # Register with prefixed names to maintain organization
    mcp.tool(name="technical_get_rsi_analysis")(get_rsi_analysis)
    mcp.tool(name="technical_get_macd_analysis")(get_macd_analysis)
    mcp.tool(name="technical_get_support_resistance")(get_support_resistance)

    # Use enhanced versions with timeout handling and comprehensive logging
    @mcp.tool(name="technical_get_full_technical_analysis")
    async def technical_get_full_technical_analysis(ticker: str, days: int = 365):
        """
        Get comprehensive technical analysis for a given ticker with enhanced logging and timeout handling.

        This enhanced version provides:
        - Step-by-step logging for debugging
        - 25-second timeout to prevent hangs
        - Comprehensive error handling
        - Guaranteed JSON-RPC responses

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data to analyze (default: 365)

        Returns:
            Dictionary containing complete technical analysis or error information
        """
        request = TechnicalAnalysisRequest(ticker=ticker, days=days)
        return await get_full_technical_analysis_enhanced(request)

    @mcp.tool(name="technical_get_stock_chart_analysis")
    async def technical_get_stock_chart_analysis(ticker: str):
        """
        Generate a comprehensive technical analysis chart with enhanced error handling.

        This enhanced version provides:
        - 15-second timeout for chart generation
        - Progressive chart sizing for Claude Desktop compatibility
        - Detailed logging for debugging
        - Graceful fallback on errors

        Args:
            ticker: The ticker symbol of the stock to analyze

        Returns:
            Dictionary containing chart data or error information
        """
        return await get_stock_chart_analysis_enhanced(ticker)


def register_screening_tools(mcp: FastMCP) -> None:
    """Register screening tools directly on main server"""
    from maverick_mcp.api.routers.screening import (
        get_all_screening_recommendations,
        get_maverick_bear_stocks,
        get_maverick_stocks,
        get_screening_by_criteria,
        get_supply_demand_breakouts,
    )

    mcp.tool(name="screening_get_maverick_stocks")(get_maverick_stocks)
    mcp.tool(name="screening_get_maverick_bear_stocks")(get_maverick_bear_stocks)
    mcp.tool(name="screening_get_supply_demand_breakouts")(get_supply_demand_breakouts)
    mcp.tool(name="screening_get_all_screening_recommendations")(
        get_all_screening_recommendations
    )
    mcp.tool(name="screening_get_screening_by_criteria")(get_screening_by_criteria)


def register_portfolio_tools(mcp: FastMCP) -> None:
    """Register portfolio tools directly on main server"""
    from maverick_mcp.api.routers.portfolio import (
        compare_tickers,
        portfolio_correlation_analysis,
        risk_adjusted_analysis,
    )

    mcp.tool(name="portfolio_risk_adjusted_analysis")(risk_adjusted_analysis)
    mcp.tool(name="portfolio_compare_tickers")(compare_tickers)
    mcp.tool(name="portfolio_portfolio_correlation_analysis")(
        portfolio_correlation_analysis
    )


def register_data_tools(mcp: FastMCP) -> None:
    """Register data tools directly on main server"""
    from maverick_mcp.api.routers.data import (
        clear_cache,
        fetch_stock_data,
        fetch_stock_data_batch,
        get_cached_price_data,
        get_chart_links,
        get_stock_info,
    )

    # Import enhanced news sentiment that uses Tiingo or LLM
    from maverick_mcp.api.routers.news_sentiment_enhanced import (
        get_news_sentiment_enhanced,
    )

    mcp.tool(name="data_fetch_stock_data")(fetch_stock_data)
    mcp.tool(name="data_fetch_stock_data_batch")(fetch_stock_data_batch)
    mcp.tool(name="data_get_stock_info")(get_stock_info)

    # Use enhanced news sentiment that doesn't rely on EXTERNAL_DATA_API_KEY
    @mcp.tool(name="data_get_news_sentiment")
    async def get_news_sentiment(ticker: str, timeframe: str = "7d", limit: int = 10):
        """
        Get news sentiment analysis for a stock using Tiingo News API or LLM analysis.

        This enhanced tool provides reliable sentiment analysis by:
        - Using Tiingo's news API if available (requires paid plan)
        - Analyzing sentiment with LLM (Claude/GPT)
        - Falling back to research-based sentiment
        - Never failing due to missing EXTERNAL_DATA_API_KEY

        Args:
            ticker: Stock ticker symbol
            timeframe: Time frame for news (1d, 7d, 30d, etc.)
            limit: Maximum number of news articles to analyze

        Returns:
            Dictionary containing sentiment analysis with confidence scores
        """
        return await get_news_sentiment_enhanced(ticker, timeframe, limit)

    mcp.tool(name="data_get_cached_price_data")(get_cached_price_data)
    mcp.tool(name="data_get_chart_links")(get_chart_links)
    mcp.tool(name="data_clear_cache")(clear_cache)


def register_trend_analysis_tools(mcp: FastMCP) -> None:
    """Register trend analysis tools directly on main server"""
    from maverick_mcp.tools.trend_scorer import (
        BatchTrendScoreInput,
        TrendScoreInput,
        trend_scorer,
    )

    @mcp.tool(name="trend_calculate_single_score")
    async def calculate_single_trend_score(
        ticker: str, 
        period: str = "6mo", 
        fixed_end_date: str = None
    ):
        """
        计算单个股票的趋势评分
        
        基于5个技术指标（MA、MACD、ADX、RSI、OBV）计算综合趋势分数：
        - 移动平均线 (MA): 评分范围 (-3, 3)
        - MACD: 评分范围 (-2, 2)  
        - ADX: 评分范围 (-2, 2)
        - RSI: 评分范围 (-1, 1)
        - OBV: 评分范围 (-1, 1)
        
        总评分范围: -9到+9，标准化为0-100分
        
        Args:
            ticker: 股票代码
            period: 数据期间 (1mo, 3mo, 6mo, 1y, 2y)
            fixed_end_date: 固定截止日期 YYYY-MM-DD (可选)
            
        Returns:
            Dictionary containing trend score analysis
        """
        # 创建带固定日期的评分器实例
        scorer = trend_scorer.__class__(fixed_end_date=fixed_end_date)
        
        result = scorer.calculate_trend_score(ticker.upper(), period)
        if not result:
            return {
                "error": f"无法获取 {ticker} 的数据或数据不足",
                "ticker": ticker.upper(),
                "period": period
            }
        
        return result.model_dump()

    @mcp.tool(name="trend_calculate_batch_scores")
    async def calculate_batch_trend_scores(
        tickers: str,  # JSON string of ticker list
        period: str = "6mo",
        fixed_end_date: str = None
    ):
        """
        批量计算多个股票的趋势评分
        
        Args:
            tickers: 股票代码列表的JSON字符串，例如: '["AAPL", "MSFT", "GOOGL"]'
            period: 数据期间 (1mo, 3mo, 6mo, 1y, 2y)
            fixed_end_date: 固定截止日期 YYYY-MM-DD (可选)
            
        Returns:
            List of dictionaries containing trend score analysis for each ticker
        """
        import json
        try:
            ticker_list = json.loads(tickers)
            if not isinstance(ticker_list, list):
                return {"error": "tickers 参数必须是股票代码列表的JSON字符串"}
        except json.JSONDecodeError:
            return {"error": "无效的JSON格式"}
        
        # 创建带固定日期的评分器实例
        scorer = trend_scorer.__class__(fixed_end_date=fixed_end_date)
        
        # 标准化股票代码
        ticker_list = [t.upper() for t in ticker_list]
        
        results = scorer.calculate_batch_scores(ticker_list, period)
        
        if not results:
            return {
                "error": "无法获取任何股票的数据",
                "tickers": ticker_list,
                "period": period
            }
        
        return {
            "results": [r.model_dump() for r in results],
            "summary": {
                "total_processed": len(results),
                "highest_score": max(r.normalized_trend_score for r in results),
                "lowest_score": min(r.normalized_trend_score for r in results),
                "average_score": sum(r.normalized_trend_score for r in results) / len(results)
            }
        }

    @mcp.tool(name="trend_get_score_explanation")
    async def get_trend_score_explanation():
        """
        获取趋势评分系统的详细说明
        
        Returns:
            Dictionary explaining the trend scoring methodology
        """
        return {
            "system_overview": "S&P 500趋势评分系统基于5个技术指标计算综合趋势分数",
            "indicators": {
                "MA": {
                    "name": "移动平均线",
                    "range": "(-3, 3)",
                    "description": "基于20日和50日移动平均线的相对位置"
                },
                "MACD": {
                    "name": "MACD指标",
                    "range": "(-2, 2)",
                    "description": "基于MACD线与信号线的关系"
                },
                "ADX": {
                    "name": "ADX趋势强度",
                    "range": "(-2, 2)",
                    "description": "基于ADX值和+DI/-DI的关系"
                },
                "RSI": {
                    "name": "相对强弱指标",
                    "range": "(-1, 1)",
                    "description": "基于RSI的超买超卖区间"
                },
                "OBV": {
                    "name": "成交量平衡指标",
                    "range": "(-1, 1)",
                    "description": "基于最近5天的OBV趋势"
                }
            },
            "scoring_method": {
                "raw_score_range": "(-9, 9)",
                "normalized_range": "(0, 100)",
                "weight_per_indicator": 0.2333,
                "formula": "标准化分数 = (加权原始分数 + 2.1) / 4.2 * 100"
            },
            "interpretation": {
                "80-100": "强烈看涨",
                "60-79": "看涨",
                "40-59": "中性",
                "20-39": "看跌",
                "0-19": "强烈看跌"
            }
        }


def register_performance_tools(mcp: FastMCP) -> None:
    """Register performance tools directly on main server"""
    from maverick_mcp.api.routers.performance import (
        analyze_database_index_usage,
        clear_system_caches,
        get_cache_performance_status,
        get_database_performance_status,
        get_redis_health_status,
        get_system_performance_health,
        optimize_cache_configuration,
    )

    mcp.tool(name="performance_get_system_performance_health")(
        get_system_performance_health
    )
    mcp.tool(name="performance_get_redis_health_status")(get_redis_health_status)
    mcp.tool(name="performance_get_cache_performance_status")(
        get_cache_performance_status
    )
    mcp.tool(name="performance_get_database_performance_status")(
        get_database_performance_status
    )
    mcp.tool(name="performance_analyze_database_index_usage")(
        analyze_database_index_usage
    )
    mcp.tool(name="performance_optimize_cache_configuration")(
        optimize_cache_configuration
    )
    mcp.tool(name="performance_clear_system_caches")(clear_system_caches)


def register_agent_tools(mcp: FastMCP) -> None:
    """Register agent tools directly on main server if available"""
    try:
        from maverick_mcp.api.routers.agents import (
            analyze_market_with_agent,
            compare_multi_agent_analysis,
            compare_personas_analysis,
            deep_research_financial,
            get_agent_streaming_analysis,
            list_available_agents,
            orchestrated_analysis,
        )

        # Original agent tools
        mcp.tool(name="agents_analyze_market_with_agent")(analyze_market_with_agent)
        mcp.tool(name="agents_get_agent_streaming_analysis")(
            get_agent_streaming_analysis
        )
        mcp.tool(name="agents_list_available_agents")(list_available_agents)
        mcp.tool(name="agents_compare_personas_analysis")(compare_personas_analysis)

        # New orchestration tools
        mcp.tool(name="agents_orchestrated_analysis")(orchestrated_analysis)
        mcp.tool(name="agents_deep_research_financial")(deep_research_financial)
        mcp.tool(name="agents_compare_multi_agent_analysis")(
            compare_multi_agent_analysis
        )
    except ImportError:
        # Agents module not available
        pass


def register_research_tools(mcp: FastMCP) -> None:
    """Register deep research tools directly on main server"""
    try:
        # Import all research tools from the consolidated research module
        from maverick_mcp.api.routers.research import (
            CompanyResearchRequest,
            ResearchRequest,
            SentimentAnalysisRequest,
            analyze_market_sentiment,
            company_comprehensive_research,
            comprehensive_research,
            get_research_agent,
        )

        # Register comprehensive research tool with all enhanced features
        @mcp.tool(name="research_comprehensive_research")
        async def research_comprehensive(request: ResearchRequest) -> dict:
            """
            Perform comprehensive research on any financial topic using web search and AI analysis.

            Enhanced version with:
            - Adaptive timeout based on research scope (basic: 15s, standard: 30s, comprehensive: 60s, exhaustive: 90s)
            - Step-by-step logging for debugging
            - Guaranteed responses to Claude Desktop
            - Optimized parallel execution for faster results

            Perfect for researching stocks, sectors, market trends, company analysis.
            """
            return await comprehensive_research(
                query=request.query,
                persona=request.persona or "moderate",
                research_scope=request.research_scope or "standard",
                max_sources=min(
                    request.max_sources or 25, 25
                ),  # Increased cap due to adaptive timeout
                timeframe=request.timeframe or "1m",
            )

        # Enhanced sentiment analysis (imported above)
        @mcp.tool(name="research_analyze_market_sentiment")
        async def analyze_market_sentiment_tool(
            request: SentimentAnalysisRequest,
        ) -> dict:
            """
            Analyze market sentiment for stocks, sectors, or market trends.

            Enhanced version with:
            - 20-second timeout protection
            - Streamlined execution for speed
            - Step-by-step logging for debugging
            - Guaranteed responses
            """
            return await analyze_market_sentiment(
                topic=request.topic,
                timeframe=request.timeframe or "1w",
                persona=request.persona or "moderate",
            )

        # Enhanced company research (imported above)

        @mcp.tool(name="research_company_comprehensive")
        async def research_company_comprehensive(
            request: CompanyResearchRequest,
        ) -> dict:
            """
            Perform comprehensive company research and fundamental analysis.

            Enhanced version with:
            - 20-second timeout protection to prevent hanging
            - Streamlined analysis for faster execution
            - Step-by-step logging for debugging
            - Focus on core financial metrics
            - Guaranteed responses to Claude Desktop
            """
            return await company_comprehensive_research(
                symbol=request.symbol,
                include_competitive_analysis=request.include_competitive_analysis
                or False,
                persona=request.persona or "moderate",
            )

        @mcp.tool(name="research_search_financial_news")
        async def search_financial_news(
            query: str,
            timeframe: str = "1w",
            max_results: int = 20,
            persona: str = "moderate",
        ) -> dict:
            """Search for recent financial news and analysis on any topic."""
            agent = get_research_agent()

            # Use basic research for news search
            result = await agent.research_topic(
                query=f"{query} news",
                session_id=f"news_{datetime.now().timestamp()}",
                research_scope="basic",
                max_sources=max_results,
                timeframe=timeframe,
            )

            return {
                "success": True,
                "query": query,
                "news_results": result.get("processed_sources", [])[:max_results],
                "total_found": len(result.get("processed_sources", [])),
                "timeframe": timeframe,
                "persona": persona,
            }

        logger.info("Successfully registered 4 research tools directly")

    except ImportError as e:
        logger.warning(f"Research module not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register research tools: {e}")
        # Don't raise - allow server to continue without research tools


def register_all_router_tools(mcp: FastMCP) -> None:
    """Register all router tools directly on the main server"""
    logger.info("Starting tool registration process...")

    try:
        register_technical_tools(mcp)
        logger.info("✓ Technical tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register technical tools: {e}")

    try:
        register_screening_tools(mcp)
        logger.info("✓ Screening tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register screening tools: {e}")

    try:
        register_portfolio_tools(mcp)
        logger.info("✓ Portfolio tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register portfolio tools: {e}")

    try:
        register_data_tools(mcp)
        logger.info("✓ Data tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register data tools: {e}")

    try:
        register_performance_tools(mcp)
        logger.info("✓ Performance tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register performance tools: {e}")

    try:
        register_trend_analysis_tools(mcp)
        logger.info("✓ Trend analysis tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register trend analysis tools: {e}")

    try:
        register_agent_tools(mcp)
        logger.info("✓ Agent tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register agent tools: {e}")

    try:
        # Import and register research tools on the main MCP instance
        from maverick_mcp.api.routers.research import create_research_router

        # Pass the main MCP instance to register tools directly on it
        create_research_router(mcp)
        logger.info("✓ Research tools registered successfully")
    except Exception as e:
        logger.error(f"✗ Failed to register research tools: {e}")

    logger.info("Tool registration process completed")
