def calculate_margin_trading(cash: float, securities_value: float, margin_buy_amount: float, short_sell_amount: float, interest_and_fees: float, stock_concentration: dict, max_credit_line: float) -> dict:
    """
    Calculate the maximum amount that can be financed and the maximum amount that can be bought for a specific stock in margin trading.
    """
    # Calculate maintenance margin ratio
    maintenance_margin_ratio = (cash + securities_value) / (margin_buy_amount + short_sell_amount + interest_and_fees) * 100
    
    # Determine if the maintenance margin ratio is below the warning line or the liquidation line
    warning_line = 150
    liquidation_line = 130
    if maintenance_margin_ratio < warning_line:
        risk_warning = 'Risk warning: Maintenance margin ratio is below the warning line.'
    elif maintenance_margin_ratio < liquidation_line:
        risk_warning = 'Risk warning: Maintenance margin ratio is below the liquidation line. Additional margin is required, or forced liquidation will occur.'
    else:
        risk_warning = 'No risk warning.'
    
    # Calculate the maximum amount that can be financed
    max_financed_amount = max_credit_line - (margin_buy_amount + short_sell_amount + interest_and_fees)
    
    # Calculate the maximum amount that can be bought for a specific stock considering stock concentration limits
    stock_concentration_limit = stock_concentration.get('concentration_limit', 100)
    max_buy_amount = (cash + securities_value) * (stock_concentration_limit / 100)
    
    return {
        'maintenance_margin_ratio': maintenance_margin_ratio,
        'risk_warning': risk_warning,
        'max_financed_amount': max_financed_amount,
        'max_buy_amount': max_buy_amount
    }

# Define tool information
calculate_margin_trading.tool_info = {
    'tool_name': 'calculate_margin_trading',
    'tool_description': 'Calculate the maximum amount that can be financed and the maximum amount that can be bought for a specific stock in margin trading.',
    'tool_params': [
        {'name': 'cash', 'description': '账户中可用现金', 'type': 'float', 'required': True},
        {'name': 'securities_value', 'description': '账户内证券的总市值', 'type': 'float', 'required': True},
        {'name': 'margin_buy_amount', 'description': '融资购买保证金的金额', 'type': 'float', 'required': True},
        {'name': 'short_sell_amount', 'description': '为卖空融资的金额', 'type': 'float', 'required': True},
        {'name': 'interest_and_fees', 'description': '利息及费用总额', 'type': 'float', 'required': True},
        {'name': 'stock_concentration', 'description': '股票集中度限制', 'type': 'dict', 'required': True},
        {'name': 'max_credit_line', 'description': '用户授信额度', 'type': 'float', 'required': True}
    ]
}