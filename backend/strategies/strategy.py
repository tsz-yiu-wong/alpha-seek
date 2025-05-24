def get_token_tag(token_data):
    
    try:
        price_change_5m = token_data.get('priceChange_m5')
        if price_change_5m and price_change_5m > 10:
            return "buy"
    except Exception as e:
        print(f"Error in get_token_tag: {e}")
    
    return "-"  # 默认返回"-"