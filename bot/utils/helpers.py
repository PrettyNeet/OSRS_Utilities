import math

# Skill effect on yield based on OSRS wiki herb farm calculator
def skill_interp(low, high, level):
    value = (low * (99 - level) / 98) + (high * (level - 1) / 98) + 1
    return min(max(value / 256, 0), 1)

# Calculate the estimated yield based on farming level and bonuses
def generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus):
    low_cts_final = math.floor(low_cts * (1 + item_bonus))
    low_cts_final += diary_bonus
    low_cts_final = math.floor(low_cts_final * (1 + attas_bonus))
    
    high_cts_final = math.floor(high_cts * (1 + item_bonus))
    high_cts_final += diary_bonus
    high_cts_final = math.floor(high_cts_final * (1 + attas_bonus))
    
    chance_to_save = skill_interp(low_cts_final, high_cts_final, farming_level)
    return harvest_lives / (1 - chance_to_save)

# Format the profit results into a markdown table
def format_profit_table(profit_results):
    headers = ["Herb", "Seed Price", "Grimy Herb Price", "Potential Yield", "Profit per Seed", "Profit per Run"]
    table = f"{' | '.join(headers)}\n"
    table += f"{' | '.join(['-' * len(header) for header in headers])}\n"
    for result in profit_results:
        row = [str(result[header]) for header in headers]
        table += f"{' | '.join(row)}\n"
    return table
