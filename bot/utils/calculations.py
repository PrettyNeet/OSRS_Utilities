from bot.utils.helpers import generate_estimated_yield
from bot.utils.logger import setup_logging

# setup the logger
logger = setup_logging()


# Calculate profit based on user inputs and real-time prices
def calculate_custom_profit(prices, herbs, farming_level, patches, weiss, trollheim, hosidius, fortis, compost, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket, attas, price_key):
    # Constants and multipliers
    compost_life_value = {'None': 0, 'Compost': 1, 'Supercompost': 2, 'Ultracompost': 3}
    item_bonus = 0.1 if magic_secateurs else 0
    item_bonus += 0.05 if farming_cape else 0
    kandarin_bonus = float(kandarin_diary.split('%')[0]) / 100 if kandarin_diary != 'None' else 0
    kourend_bonus = 0.05 if kourend else 0
    diary_bonus = kandarin_bonus + kourend_bonus
    compost_life = compost_life_value.get(compost, 0)
    attas_bonus = 0.05 if attas else 0  # Assuming animaType can be checked similarly

    # Disease removed since we do not resurrect crops

    # Adjust patches based on disease-free options
    protected_patches = 0
    protected_names = []
    if weiss:
        protected_patches += 1
        protected_names.append('Weiss')
    if trollheim:
        protected_patches += 1
        protected_names.append('Trollheim')
    if hosidius:
        protected_patches += 1
        protected_names.append('Hosidius')
    if fortis:
        protected_patches += 1
        protected_names.append('Civitas illa Fortis')

    unprotected_patches = patches - protected_patches

    results = []
    for herb, info in herbs.items():
        seed_id_str = str(info["seed_id"])
        herb_id_str = str(info["herb_id"])
        low_cts = info["lowCTS"]
        high_cts = 80
        harvest_lives = 3 + compost_life

        if seed_id_str not in prices or herb_id_str not in prices:
            continue

        seed_price = prices[seed_id_str][price_key]
        herb_price = prices[herb_id_str][price_key]
        
        logger.debug("price type: %s", {price_key})
        logger.debug("Herb: %s", {herb}, "Seed Price: %s", {seed_price}, "Herb Price: %s", {herb_price})
            
        if seed_price is None or herb_price is None:
            continue

        # Calculate expected yield using detailed mechanics
        expected_yield_unprotected = generate_estimated_yield(
            farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus)

        # Calculate total yield and profit for unprotected patches
        total_yield_unprotected = expected_yield_unprotected * unprotected_patches
        
        # Calculate expected yield for protected patches
        total_yield_protected = 0
        expected_yield_protected = 0
        if protected_patches > 0:
            for _ in range(protected_patches):
                if "Hosidius" in protected_names and kourend:
                    expected_yield_protected = generate_estimated_yield(
                        farming_level, low_cts, high_cts, harvest_lives, item_bonus, kourend_bonus, attas_bonus)
                else:  # change logic to check for kandarin patches (Catherby)
                    expected_yield_protected = generate_estimated_yield(
                        farming_level, low_cts, high_cts, harvest_lives, item_bonus, kandarin_bonus, attas_bonus)
                total_yield_protected += expected_yield_protected
        
        total_patches = unprotected_patches + protected_patches
        
        total_yield = total_yield_unprotected + total_yield_protected
        profit_per_run = (herb_price * total_yield) - (seed_price * total_patches)

        # Debug print statements
        logger.debug("Herb:", {herb})
        logger.debug("Seed Price:", {seed_price})
        logger.debug("Herb Price:", {herb_price})
        logger.debug("CTSLow:", {low_cts})
        logger.debug("Expected Yield (Unprotected):", {expected_yield_unprotected})
        logger.debug("Expected Yield (Protected):", {expected_yield_protected})
        logger.debug("Total Yield (Unprotected):", {total_yield_unprotected})
        logger.debug("Total Yield (Protected):", {total_yield_protected})
        logger.debug("Total Yield:", {total_yield})
        logger.debug("Total Patches:", {total_patches})
        logger.debug("Profit per Run:", {profit_per_run})

        results.append({
            "Herb": herb,
            "Seed Price": seed_price,
            "Grimy Herb Price": herb_price,
            "Profit per Run": profit_per_run
        })

    return results
