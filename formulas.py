"""
Formula calculations for sake brewing
Based on rules.txt specifications
"""
from typing import Optional, Tuple


def calculate_final_gravity(
    measured_temp_C: float,
    measured_gravity: float,
    calibrated_temp_C: float = 20.0
) -> Optional[float]:
    """
    Calculate corrected final gravity based on temperature
    Formula from rules.txt:
    if(not(isblank(final_measured_temp_C)), 
        LET(mt, INDEX(final_measured_temp_C, ROW()), 
            mg, INDEX(final_measured_gravity, ROW()), 
            ct, 20, 
            pmt, 0.999005559846799 - 0.000020305299748608*mt + 0.0000058871378337408*mt^2 - 0.00000001357811768736*mt^3, 
            pct, 0.999005559846799 - 0.000020305299748608*ct + 0.0000058871378337408*ct^2 - 0.00000001357811768736*ct^3, 
            ROUND(mg * pmt / pct, 4)),"")
    """
    if measured_temp_C is None or measured_gravity is None:
        return None
    
    mt = measured_temp_C
    mg = measured_gravity
    ct = calibrated_temp_C
    
    # Calculate water density at measured temperature
    pmt = (0.999005559846799 - 
           0.000020305299748608 * mt + 
           0.0000058871378337408 * mt**2 - 
           0.00000001357811768736 * mt**3)
    
    # Calculate water density at calibrated temperature
    pct = (0.999005559846799 - 
           0.000020305299748608 * ct + 
           0.0000058871378337408 * ct**2 - 
           0.00000001357811768736 * ct**3)
    
    # Correct gravity
    corrected_gravity = round(mg * pmt / pct, 4)
    return corrected_gravity


def calculate_abv(
    brix_pct: float,
    final_gravity: float
) -> Optional[float]:
    """
    Calculate ABV% from brix and final gravity
    Formula from rules.txt:
    if(not(isblank(final_measured_temp_C)), 
        let(b, index(final_measured_Brix_%, ROW()), 
            fg, index(final_gravity, ROW()), 
            round(1.646*b-2.703*(145-145/fg)-1.794,1)),"")
    """
    if brix_pct is None or final_gravity is None:
        return None
    
    b = brix_pct
    fg = final_gravity
    
    abv = round(1.646 * b - 2.703 * (145 - 145 / fg) - 1.794, 1)
    return abv


def calculate_smv(final_gravity: float) -> Optional[float]:
    """
    Calculate SMV (Sake Meter Value) from final gravity
    Formula from rules.txt:
    if(not(isblank(final_measured_temp_C)), 
        let(fg, index(final_gravity, ROW()), 
            ROUND(1443/fg-1443,1)), "")
    """
    if final_gravity is None:
        return None
    
    smv = round(1443 / final_gravity - 1443, 1)
    return smv


def calculate_dilution_adjustment(
    current_brix: float,
    current_gravity: float,
    target_brix: float,
    target_gravity: float,
    current_volume_L: float,
    fortifier_brix: float = 35.0,
    fortifier_gravity: Optional[float] = None,
) -> dict:
    """
    Calculate dilution/addition guidance matching rules.txt.

    If the target brix is higher than the current brix we assume amazake
    (default 35°Bx) is added; otherwise we fall back to water dilution.
    """

    def _water_addition() -> Tuple[float, float, float]:
        if current_brix <= 0:
            return 0.0, current_brix, current_gravity
        dilution_factor = target_brix / current_brix
        water_to_add = current_volume_L * (1 / dilution_factor - 1)
        if water_to_add < 0:
            water_to_add = 0.0
        final_volume = current_volume_L + water_to_add
        if final_volume <= 0:
            return water_to_add, current_brix, current_gravity
        final_brix = (current_brix * current_volume_L) / final_volume
        final_gravity = (current_gravity * current_volume_L) / final_volume
        return water_to_add, final_brix, final_gravity

    def _amazake_addition() -> Tuple[float, float, float]:
        additive_gravity = (
            fortifier_gravity
            if fortifier_gravity
            else 1 + (fortifier_brix / (258.6 - ((fortifier_brix / 258.2) * 227.1)))
        )
        numerator = current_volume_L * (target_brix - current_brix)
        denominator = fortifier_brix - target_brix
        if denominator <= 0:
            return _water_addition()
        addition_volume = max(numerator / denominator, 0.0)
        final_volume = current_volume_L + addition_volume
        if final_volume <= 0:
            return addition_volume, current_brix, current_gravity
        final_brix = (
            (current_brix * current_volume_L + fortifier_brix * addition_volume) / final_volume
        )
        final_gravity = (
            (current_gravity * current_volume_L + additive_gravity * addition_volume) / final_volume
        )
        return addition_volume, final_brix, final_gravity

    use_amazake = target_brix >= current_brix
    if use_amazake:
        addition_volume, final_brix, final_gravity = _amazake_addition()
        addition_label = "amazake"
    else:
        addition_volume, final_brix, final_gravity = _water_addition()
        addition_label = "water"

    final_volume_L = current_volume_L + addition_volume

    rounded_addition = round(addition_volume, 2)
    return {
        'addition_type': addition_label,
        'volume_to_add_L': rounded_addition,
        'water_to_add_L': rounded_addition,
        'final_volume_L': round(final_volume_L, 2),
        'final_brix': round(final_brix, 2),
        'final_gravity': round(final_gravity, 4),
        'target_brix': target_brix,
        'target_gravity': target_gravity,
    }
