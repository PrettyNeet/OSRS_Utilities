import requests
import math
from config.settings import HEADERS, DEBUG

#grabs latest prices from wiki API, returns the entire list of all items to save an API resource
def fetch_latest_prices():
    url = "https://prices.runescape.wiki/api/v1/osrs/latest"
    response = requests.get(url, headers=HEADERS) #osrs wiki demands custom user-agent headers, defined in config.yaml. python requests are blocked by default
    data = response.json()

    if "data" not in data:
        raise ValueError("Error fetching data from API")
    return data["data"]

#skill effect on yield based on osrs wiki herb farm calculator
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

# Calculate profit based on user inputs and real-time prices
def calculate_custom_profit(prices, herbs, farming_level, patches, weiss, trollheim, hosidius, fortis, compost, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket):
    # Constants and multipliers
    compost_chance_reduction = {'None': 1, 'Compost': 2, 'Supercompost': 5, 'Ultracompost': 10}
    compost_life_value = {'None': 0, 'Compost': 1, 'Supercompost': 2, 'Ultracompost': 3}
    item_bonus = 0.1 if magic_secateurs else 0
    item_bonus += 0.05 if farming_cape else 0
    kandarin_bonus = float(kandarin_diary.split('%')[0])/100 if kandarin_diary != 'None' else 0
    kourend_bonus = 0.05 if kourend else 0
    compost_bonus = compost_chance_reduction.get(compost, 1)
    compost_life = compost_life_value.get(compost, 0)
    attas_bonus = 0.05 if "attas" else 0  # Assuming animaType can be checked similarly

    # Disease and yield calculation
    death_rate_per_stage = (math.floor(27 / compost_bonus) + 1) / 128
    patch_survival_rate = (1 - death_rate_per_stage) ** 3
    patch_death_rate = 1 - patch_survival_rate

    # Adjust patches based on disease-free options
    protected_patches = 0
    if weiss:
        protected_patches += 1
    if trollheim:
        protected_patches += 1
    if hosidius:
        protected_patches += 1
    if fortis:
        protected_patches += 1

    unprotected_patches = patches - protected_patches

    results = []
    for herb, info in herbs.items():
        seed_id_str = str(info["seed_id"])
        herb_id_str = str(info["herb_id"])

        if seed_id_str not in prices or herb_id_str not in prices:
            continue

        seed_price = prices[seed_id_str]["high"]
        herb_price = prices[herb_id_str]["high"]

        # Calculate expected yield using detailed mechanics
        expected_yield_unprotected = generate_estimated_yield(farming_level, 25, 80, 3 + compost_life, item_bonus, kandarin_bonus + kourend_bonus, attas_bonus)
        expected_yield_protected = generate_estimated_yield(farming_level, 25, 80, 3 + compost_life, item_bonus, kandarin_bonus + kourend_bonus, attas_bonus)

        # Calculate total yield and profit per run
        total_yield_unprotected = expected_yield_unprotected * unprotected_patches
        total_yield_protected = expected_yield_protected * protected_patches
        total_patches = unprotected_patches + protected_patches
        
        total_yield = total_yield_unprotected + total_yield_protected
        profit_per_run = (herb_price * total_yield) - (seed_price * total_patches)

        # Debug print statements
        if DEBUG:
            print(f"Herb: {herb}")
            print(f"Seed Price: {seed_price}")
            print(f"Herb Price: {herb_price}")
            print(f"Expected Yield (Unprotected): {expected_yield_unprotected}")
            print(f"Expected Yield (Protected): {expected_yield_protected}")
            print(f"Total Yield (Unprotected): {total_yield_unprotected}")
            print(f"Total Yield (Protected): {total_yield_protected}")
            print(f"Total Yield: {total_yield}")
            print(f"Total Patches: {total_patches}")
            print(f"Profit per Run: {profit_per_run}")
            print("-" * 40)

        results.append({
            "Herb": herb,
            "Seed Price": seed_price,
            "Grimy Herb Price": herb_price,
            "Profit per Run": profit_per_run
        })

    return results
