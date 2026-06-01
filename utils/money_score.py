def calculate_money_score(income, expenses, savings, investments, debt, emergency_fund):

    score = 0

    # 1. Savings Rate (30)
    savings_rate = savings / income if income > 0 else 0.0
    if savings_rate >= 0.3:
        score += 30
    elif savings_rate >= 0.2:
        score += 20
    else:
        score += 10

    # 2. Investment Rate (25)
    invest_rate = investments / income if income > 0 else 0.0
    if invest_rate >= 0.2:
        score += 25
    elif invest_rate >= 0.1:
        score += 15
    else:
        score += 5

    # 3. Debt Ratio (25)
    debt_ratio = debt / income if income > 0 else (1.0 if debt > 0 else 0.0)
    if debt_ratio <= 0.2:
        score += 25
    elif debt_ratio <= 0.4:
        score += 15
    else:
        score += 5

    # 4. Emergency Fund (20)
    months_cover = emergency_fund / expenses if expenses > 0 else (12.0 if emergency_fund > 0 else 0.0)
    if months_cover >= 6:
        score += 20
    elif months_cover >= 3:
        score += 10
    else:
        score += 5

    return round(score)