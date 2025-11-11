"""
Formula calculations for sake brewing
Based on rules.txt specifications
"""
from typing import Optional


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
    current_volume_L: float
) -> dict:
    """
    Calculate dilution needed to reach target profile
    Returns dict with:
    - water_to_add_L: volume of water to add
    - final_volume_L: final volume after dilution
    - final_brix: estimated final brix
    - final_gravity: estimated final gravity
    """
    # This is a simplified calculation
    # More complex calculations would be needed for precise adjustments
    
    # Estimate water needed (simplified linear approximation)
    brix_diff = current_brix - target_brix
    gravity_diff = current_gravity - target_gravity
    
    # Rough estimate - would need more sophisticated formula
    if brix_diff > 0:
        # Need to dilute
        dilution_factor = target_brix / current_brix if current_brix > 0 else 1
        water_to_add_L = current_volume_L * (1 / dilution_factor - 1)
    else:
        water_to_add_L = 0
    
    final_volume_L = current_volume_L + water_to_add_L
    final_brix = (current_brix * current_volume_L) / final_volume_L if final_volume_L > 0 else current_brix
    final_gravity = (current_gravity * current_volume_L) / final_volume_L if final_volume_L > 0 else current_gravity
    
    return {
        'water_to_add_L': round(water_to_add_L, 2),
        'final_volume_L': round(final_volume_L, 2),
        'final_brix': round(final_brix, 2),
        'final_gravity': round(final_gravity, 4)
    }




