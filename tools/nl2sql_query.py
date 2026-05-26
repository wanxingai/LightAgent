import mysql.connector
from openai import OpenAI


def nl2sql_query(user_query: str) -> str:
    """
    将自然语言查询转换为SQL并在MySQL数据库上执行

    参数:
        user_query (str): 用户提供的自然语言查询

    返回:
        str: SQL查询执行结果
    """

    # 证券公司业务数据表结构
    table_structure = """
    数据库表结构说明：
    1. 总部数据表 (ZB_V2)
- TRADEDATE              业务日期（主键）
- CNT_CREDIT             信用客户总数
- CNT_CREDIT_GR          信用个人客户总数
- CNT_CREDIT_ORG         信用机构客户总数
- CNT_CREDIT_PROD        信用产品客户总数
- CNT_CREDIT_XK          当年新开客户数
- CNT_CREDIT_CLXK        当年存量新开客户数
- CNT_CREDIT_WBXK        当年外部新开客户数
- CNT_CREDIT_CLXK_YX     当年存量新开有效客户数
- CNT_CREDIT_WBXK_YX     当年外部新开有效客户数
- CNT_CREDIT_XK_YX       当年新开有效客户数
- CNT_CREDIT_XK_YX_RATE  当年新开有效客户率
- CNT_CREDIT_XK_MKT      市场当年新开客户数
- CNT_CREDIT_XK_RATE     当年新开客户数市占率
- CNT_CREDIT_XK_RATE_CHG 当年新开客户数市占率较去年年末变化
- CNT_CREDIT_CLOSED      销户客户数
- CNT_CREDIT_CLOSED_MKT  市场当年销户客户数
- CNT_CREDIT_CLOSED_RATE 当年销户客户数市占率
- CNT_CREDIT_CLOSED_RATE_CHG 当年销户客户数市占率较去年年末变化
- CLOSED_LOSS_BALANCE_RZRQ 当年销户客户流失融资融券余额
- CNT_CREDIT_CLOSED_YX    销户有效客户数
- CNT_CREDIT_CLOSED_YX_RATE 当年销户有效客户率
- CNT_CREDIT_NET_NEW      当年净新增客户数
- CNT_NET_XK_MKT          市场当年净新开客户数
- CNT_NET_XK_RATIO        净新增客户数市占率
- CNT_NET_XK_RATIO_CHG    净新增客户数市占率较去年变化
- TG_CNT_CREDIT_NET_NEW   【目标】当年净新增客户数
- JD_CNT_CREDIT_NET_NEW   【进度】当年净新增客户数
- CNT_FG_CUST             时点富高客户数
- CNT_FG_CUST_XY          时点富高客户数信用
- CNT_FG_OPRATE           富高信用客户开通率（富高信用/富高）
- BALANCE_RZRQ            两融余额（元）
- BALANCE_RZRQ_MKT        市场两融余额
- BALANCE_RZRQ_RATE       两融余额市占率
- AVG_BALANCE_RZRQ        日均两融余额（今年以来）
- AVG_BALANCE_RZRQ_MKT    市场日均两融余额（今年以来）
- AVG_BALANCE_RZRQ_RATE   日均两融余额市占率（今年以来）
- AVG_BALANCE_RZRQ_RATE_CHG 日均两融余额市占率较去年变化
- BALANCE_RZ              融资余额
- BALANCE_RZ_MKT          市场融资余额
- BALANCE_RZ_RATE         融资余额市占率
- AVG_BALANCE_RZ          日均融资余额（今年以来）
- AVG_BALANCE_RZ_MKT      市场日均融资余额（今年以来）
- AVG_BALANCE_RZ_RATE     日均融资余额市占率（今年以来）
- AVG_BALANCE_RZ_RATE_CHG 日均融资余额市占率较去年变化
- TG_AVG_BALANCE_RZ_RATE  【目标】日均融资余额市占率（今年以来）
- JD_AVG_BALANCE_RZ_RATE  【进度】日均融资余额市占率（今年以来）
- BALANCE_RQ              融券余额
- BALANCE_RQ_MKT          市场融券余额
- BALANCE_RQ_RATE         融券余额市占率
- AVG_BALANCE_RQ          日均融券余额（今年以来）
- AVG_BALANCE_RQ_MKT      市场日均融券余额（今年以来）
- AVG_BALANCE_RQ_RATE     日均融券余额市占率（今年以来）
- AVG_BALANCE_RQ_RATE_CHG 日均融券余额市占率较去年变化
- TG_AVG_BALANCE_RQ_RATE  【目标】日均融券余额市占率（今年以来）
- JD_AVG_BALANCE_RQ_RATE  【进度】日均融券余额市占率（今年以来）
- BALANCE_RZ_GR           个人客户融资余额
- BALANCE_RZ_GR_RATE      个人客户融资余额市占率
- BALANCE_RZ_ORG          机构客户融资余额
- BALANCE_RZ_ORG_RATE     机构客户融资余额市占率
- BALANCE_RZ_PROD         产品客户融资余额
- BALANCE_RZ_PROD_RATE    产品客户融资余额市占率
- AVG_BALANCE_RZ_GR       个人客户日均融资余额（今年以来）
- AVG_BALANCE_RZ_GR_RATE  个人客户日均融资余额市占率（今年以来）
- AVG_BALANCE_RZ_ORG      机构客户日均融资余额（今年以来）
- AVG_BALANCE_RZ_ORG_RATE 机构客户日均融资余额市占率（今年以来）
- AVG_BALANCE_RZ_PROD     产品客户日均融资余额（今年以来）
- AVG_BALANCE_RZ_PROD_RATE 产品客户日均融资余额市占率（今年以来）
- AVG_RZ_RATE             当前区间累计平均融资利率
- AVG_RZ_RATE_CHG         当前区间累计平均融资利率较去年年末变化
- AVG_RZ_RATE_CHG_RATE    平均融资利率变动
- AVG_RZ_RATE_CL          当前区间存量客户累计平均融资利率
- AVG_RZ_RATE_XK          当前区间新开客户累计平均融资利率
- AVG_RZ_RATE_GR          个人客户当前区间累计平均融资利率
- AVG_RZ_RATE_ORG         机构客户当前区间累计平均融资利率
- AVG_RZ_RATE_PROD        产品客户当前区间累计平均融资利率
- AVG_RZ_RATE_DY          客户当月区间累计平均融资利率
- AVG_RZ_RATE_GR_DY       个人客户当月区间累计平均融资利率
- AVG_RZ_RATE_ORG_DY      机构客户当月区间累计平均融资利率
- AVG_RZ_RATE_PROD_DY     产品客户当月区间累计平均融资利率
- NET_COMMI_CREDIT        总公司信用账户净佣金
- FEE_RZ                  累计融资利息
- FEE_RQ                  累计融券费用
- FEE_RQ_SQGL             累计融券锁券管理费
- NET_FEE_RZ              累计融资息差
- NET_FEE_RQ              累计融券息差
- JSR_TOTAL               累计净收入（净佣金+融资息差+融券息差）
- TG_JSR_TOTAL            【目标】累计净收入
- JD_JSR_TOTAL            【进度】累计净收入（目标值*月份/12）
- NET_FEE_TOTAL           累计息费净收入
- CNT_XK_GR               个人客户当年新开客户数
- CNT_XK_GR_RATE          个人客户当年新开客户数市占率
- CNT_CLXK_GR             个人客户存量新开新用户【a】
- CNT_CLXK_QZ_PKLY_GR     个人客户时点潜在两融户数且普开在今年前【b】
- CLXK_GR_KT_RATIO        个人客户存量新开信用户开通率【a】/ 【b】
- CNT_WBXK_GR             个人客户外部新开新用户【a】
- CNT_WBXK_FG_PKTY_GR     个人客户_时点普通富高个人且普开在今年【b】
- WBXK_GR_KT_RATIO        个人客户外部新开信用户开通率【a】/ 【b】
- CNT_DYXK_GR             个人客户当月新开信用户数
- CNT_XH_GR               个人客户当年销户客户数量
- LOSS_BALANCE_GR         个人客户销户客户流失余额
- CNT_DYXH_GR             个人客户当月销户客户数
- CNT_NET_XK_GR           个人客户当年净新开客户数
- CNT_NET_DYXK_GR         个人客户当月净新开客户数
- CNT_YXHS_GR             个人客户有效户数量
- CNT_CLXK_YXHS_GR        个人客户存量新开有效户数量
- CNT_CLXK_YXHS_GR_RATIO  个人客户存量新开有效户数量开通率
- CNT_WBXK_YXHS_GR        个人客户外部新开有效户数量
- CNT_WBXK_YXHS_GR_RATIO  个人客户外部新开有效户数量开通率
- CNT_CLXY_YXHS_GR        个人客户存量信用有效户数量
- CNT_CLXY_YXHS_GR_RATIO  个人客户存量信用有效户数量开通率
- AVG_BALANCE_RZ_GR_YXHS  个人客户有效户日均融资余额
- AVG_BALANCE_RZ_GR_YXHS_CLXK 个人客户存量新开有效户日均融资余额
- AVG_BALANCE_RZ_GR_YXHS_WBXK 个人客户外部新开有效户日均融资余额
- AVG_BALANCE_RZ_GR_YXHS_CLXY 个人客户存量信用有效户日均融资余额
- AVG_BALANCE_RZ_GR_CL    个人存量客户日均融资余额
- AVG_BALANCE_RZ_GR_XK    个人新开客户日均融资余额
- AVG_RZ_RATE_GR_CLXK     个人客户存量新开平均融资利率
- AVG_RZ_RATE_GR_WBXK     个人客户外部新开平均融资利率
- AVG_RZ_RATE_GR_CLXY     个人客户存量信用平均融资利率
- AVG_RZ_RATE_GR_CLXK_DY  个人客户存量新开平均融资利率当月
- AVG_RZ_RATE_GR_WBXK_DY  个人客户外部新开平均融资利率当月
- AVG_RZ_RATE_GR_CLXY_DY  个人客户存量信用平均融资利率当月
- FEE_RZ_GR               个人客户融资利息当年累计收入
- BALANCE_RZ_ORG_DNXK     机构客户当年新开客户融资余额
- BALANCE_RZ_ORG_CLXY     机构客户存量信用客户融资余额
- AVG_BALANCE_RZ_ORG_DNXK 机构客户当年新开客户日均融资余额
- AVG_BALANCE_RZ_ORG_CLXY 机构客户存量信用客户日均融资余额
- AVG_BALANCE_RZ_ORG_CL   机构存量客户日均融资余额
- AVG_BALANCE_RZ_ORG_XK   机构新开客户日均融资余额
- AVG_RZ_RATE_ORG_DNXK    机构客户当年新开平均融资利率
- AVG_RZ_RATE_ORG_CLXY    机构客户存量信用平均融资利率
- AVG_RZ_RATE_ORG_DNXK_DY 机构客户当年新开平均融资利率当月
- AVG_RZ_RATE_ORG_CLXY_DY 机构客户存量信用平均融资利率当月
- FEE_RZ_ORG              机构客户融资利息当年累计收入
- BALANCE_RZ_PROD_DNXK    产品客户当年新开客户融资余额
- BALANCE_RZ_PROD_CLXY    产品客户存量信用客户融资余额
- AVG_BALANCE_RZ_PROD_DNXK 产品客户当年新开客户日均融资余额
- AVG_BALANCE_RZ_PROD_CLXY 产品客户存量信用客户日均融资余额
- AVG_BALANCE_RZ_PROD_CL  产品存量客户日均融资余额
- AVG_BALANCE_RZ_PROD_XK  产品新开客户日均融资余额
- AVG_RZ_RATE_PROD_DNXK   产品客户当年新开平均融资利率
- AVG_RZ_RATE_PROD_CLXY   产品客户存量信用平均融资利率
- AVG_RZ_RATE_PROD_DNXK_DY 产品客户当年新开平均融资利率当月
- AVG_RZ_RATE_PROD_CLXY_DY 产品客户存量信用平均融资利率当月
- FEE_RZ_PROD             产品客户融资利息当年累计收入
- GROUND_TIME             落地时间
- CNT_CUST_FG_GR          个人客户富高客户数（净资产（普通+信用账户）50万以上）【-1为历史无法追溯】
- BALANCE_RZ_XK           新开客户融资余额
- BALANCE_RZ_XK_RATE      新开客户融资余额市占率
- BALANCE_RQ_XK           新开客户融券余额
- BALANCE_RQ_XK_RATE      新开客户融券余额市占率
- BALANCE_RZRQ_XK         新开客户两融余额
- BALANCE_RZRQ_XK_RATE    新开客户两融余额市占率
- BALANCE_RZ_CL           存量客户融资余额
- BALANCE_RZ_CL_RATE      存量客户融资余额市占率
- BALANCE_RQ_CL           存量客户融券余额
- BALANCE_RQ_CL_RATE      存量客户融券余额市占率
- BALANCE_RZRQ_CL         存量客户两融余额
- BALANCE_RZRQ_CL_RATE    存量客户两融余额市占率
- BALANCE_RZ_GR_XK        个人新开客户融资余额
- BALANCE_RZ_GR_XK_RATE   个人新开客户融资余额市占率
- BALANCE_RQ_GR_XK        个人新开客户融券余额
- BALANCE_RQ_GR_XK_RATE   个人新开客户融券余额市占率
- BALANCE_RZRQ_GR_XK      个人新开客户两融余额
- BALANCE_RZRQ_GR_XK_RATE 个人新开客户两融余额市占率
- BALANCE_RZ_ORG_XK_RATE  机构新开客户融资余额市占率
- BALANCE_RQ_ORG_XK       机构新开客户融券余额
- BALANCE_RQ_ORG_XK_RATE  机构新开客户融券余额市占率
- BALANCE_RZRQ_ORG_XK     机构新开客户两融余额
- BALANCE_RZRQ_ORG_XK_RATE 机构新开客户两融余额市占率
- BALANCE_RZ_PROD_XK_RATE 产品新开客户融资余额市占率
- BALANCE_RQ_PROD_XK      产品新开客户融券余额
- BALANCE_RQ_PROD_XK_RATE 产品新开客户融券余额市占率
- BALANCE_RZRQ_PROD_XK    产品新开客户两融余额
- BALANCE_RZRQ_PROD_XK_RATE 产品新开客户两融余额市占率
- BALANCE_RZ_GR_CL        个人存量客户融资余额
- BALANCE_RZ_GR_CL_RATE   个人存量客户融资余额市占率
- BALANCE_RQ_GR_CL        个人存量客户融券余额
- BALANCE_RQ_GR_CL_RATE   个人存量客户融券余额市占率
- BALANCE_RZRQ_GR_CL      个人存量客户两融余额
- BALANCE_RZRQ_GR_CL_RATE 个人存量客户两融余额市占率
- BALANCE_RZ_ORG_CL_RATE  机构存量客户融资余额市占率
- BALANCE_RQ_ORG_CL       机构存量客户融券余额
- BALANCE_RQ_ORG_CL_RATE  机构存量客户融券余额市占率
- BALANCE_RZRQ_ORG_CL     机构存量客户两融余额
- BALANCE_RZRQ_ORG_CL_RATE 机构存量客户两融余额市占率
- BALANCE_RZ_PROD_CL_RATE
    """

    # 初始化OpenAI客户端
    client = OpenAI(
        base_url="https://api.openai.com/v1",
        api_key="sk-rw1r5Z2UXzuD4FKL85BbC94aC733403380125c0f05F3A614"
    )

    # 构建系统提示词
    system_prompt = f"""你是一个专业SQL工程师，请根据以下表结构信息：
    {table_structure}
    请严格遵循以下规则：
    1. 只生成SQL语句不要添加解释
    2. 使用JOIN代替子查询
    3. 包含所有必要字段
    4. 使用规范的SQL语法"""

    # 调用大模型生成SQL
    response = client.chat.completions.create(
        model="qwen2.5-72b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.1,
    )

    sql_query = response.choices[0].message.content.strip()

    # 连接MySQL数据库
    db_connection = mysql.connector.connect(
        host="https://rm-uf61je7a7il1v4zhkoo.mysql.rds.aliyuncs.com",
        user="gtja_data",
        password="Gtja_123123@",
        database="gtja"
    )

    try:
        cursor = db_connection.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return str(result)
    finally:
        cursor.close()
        db_connection.close()


# 中文工具信息
nl2sql_query.tool_info = {
    "tool_name": "自然语言转SQL查询",
    "tool_description": "将自然语言转换为证券业务数据库的SQL查询并执行",
    "tool_params": [
        {
            "name": "user_query",
            "description": "需要转换的自然语言查询语句",
            "type": "string",
            "required": True
        }
    ]
}