"""
VAT Service
BTP-specific VAT calculation
"""
from typing import Dict, List, Any
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

# BTP VAT Rates in France
VAT_RATES = {
    "standard": 20.0,      # Taux normal - Travaux neufs, matériaux
    "intermediate": 10.0,  # Taux intermédiaire - Rénovation > 2 ans
    "reduced": 5.5,        # Taux réduit - Travaux d'amélioration énergétique
    "super_reduced": 2.1   # Taux super réduit - Cas spéciaux (DOM-TOM)
}

# VAT applicability rules for BTP
VAT_RULES = {
    "new_construction": {
        "rate": 20.0,
        "description": "Construction neuve ou extension"
    },
    "renovation_recent": {
        "rate": 20.0,
        "description": "Rénovation d'un bâtiment de moins de 2 ans"
    },
    "renovation_old": {
        "rate": 10.0,
        "description": "Rénovation d'un bâtiment de plus de 2 ans"
    },
    "energy_improvement": {
        "rate": 5.5,
        "description": "Travaux d'amélioration énergétique"
    },
    "social_housing": {
        "rate": 5.5,
        "description": "Logements sociaux"
    }
}

class VATService:
    """Service for BTP VAT calculations"""
    
    @staticmethod
    def calculate_item_vat(amount_ht: float, vat_rate: float) -> Dict[str, float]:
        """Calculate VAT for a single item"""
        amount_ht = Decimal(str(amount_ht))
        vat_rate = Decimal(str(vat_rate))
        
        vat_amount = (amount_ht * vat_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        amount_ttc = (amount_ht + vat_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            "amount_ht": float(amount_ht),
            "vat_rate": float(vat_rate),
            "vat_amount": float(vat_amount),
            "amount_ttc": float(amount_ttc)
        }
    
    @staticmethod
    def calculate_document_totals(items: List[Dict[str, Any]], 
                                  discount_type: str = None,
                                  discount_value: float = 0,
                                  retention_rate: float = 0) -> Dict[str, Any]:
        """Calculate totals for a quote or invoice"""
        subtotal_ht = Decimal('0')
        vat_breakdown = {}
        
        # Calculate subtotal and VAT by rate
        for item in items:
            quantity = Decimal(str(item.get('quantity', 1)))
            unit_price = Decimal(str(item.get('unit_price', 0)))
            vat_rate = Decimal(str(item.get('vat_rate', 20.0)))
            
            item_total_ht = (quantity * unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            subtotal_ht += item_total_ht
            
            # Accumulate VAT by rate
            rate_key = str(float(vat_rate))
            if rate_key not in vat_breakdown:
                vat_breakdown[rate_key] = {
                    "base_ht": Decimal('0'),
                    "vat_amount": Decimal('0')
                }
            vat_breakdown[rate_key]["base_ht"] += item_total_ht
        
        # Apply discount
        discount_amount = Decimal('0')
        if discount_type and discount_value:
            discount_value = Decimal(str(discount_value))
            if discount_type == 'percentage':
                discount_amount = (subtotal_ht * discount_value / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:  # fixed
                discount_amount = discount_value
        
        subtotal_after_discount = subtotal_ht - discount_amount
        
        # Calculate VAT amounts (proportionally after discount if applicable)
        total_vat = Decimal('0')
        discount_ratio = subtotal_after_discount / subtotal_ht if subtotal_ht > 0 else Decimal('1')
        
        for rate_key, vat_data in vat_breakdown.items():
            adjusted_base = (vat_data["base_ht"] * discount_ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            vat_rate = Decimal(rate_key)
            vat_amount = (adjusted_base * vat_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            vat_data["adjusted_base_ht"] = float(adjusted_base)
            vat_data["vat_amount"] = float(vat_amount)
            vat_data["base_ht"] = float(vat_data["base_ht"])
            total_vat += vat_amount
        
        total_ttc = subtotal_after_discount + total_vat
        
        # Calculate retention (retenue de garantie)
        retention_amount = Decimal('0')
        if retention_rate and retention_rate > 0:
            retention_rate = Decimal(str(retention_rate))
            retention_amount = (total_ttc * retention_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        net_to_pay = total_ttc - retention_amount
        
        return {
            "subtotal_ht": float(subtotal_ht),
            "discount_amount": float(discount_amount),
            "subtotal_after_discount": float(subtotal_after_discount),
            "total_vat": float(total_vat),
            "total_ttc": float(total_ttc),
            "retention_rate": float(retention_rate) if retention_rate else 0,
            "retention_amount": float(retention_amount),
            "net_to_pay": float(net_to_pay),
            "vat_breakdown": vat_breakdown
        }
    
    @staticmethod
    def calculate_situation_invoice(items: List[Dict[str, Any]],
                                    progress_percentage: float,
                                    previous_invoiced: float = 0,
                                    discount_type: str = None,
                                    discount_value: float = 0,
                                    retention_rate: float = 0) -> Dict[str, Any]:
        """Calculate amounts for a progress invoice (facture de situation)"""
        # First calculate the full document totals
        full_totals = VATService.calculate_document_totals(
            items, discount_type, discount_value, retention_rate=0  # Don't apply retention yet
        )
        
        # Calculate current progress amount
        progress = Decimal(str(progress_percentage)) / 100
        total_to_date_ht = (Decimal(str(full_totals["subtotal_after_discount"])) * progress).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        previous = Decimal(str(previous_invoiced))
        current_amount_ht = total_to_date_ht - previous
        
        # Calculate VAT on current amount
        vat_ratio = Decimal(str(full_totals["total_vat"])) / Decimal(str(full_totals["subtotal_after_discount"])) if full_totals["subtotal_after_discount"] > 0 else Decimal('0')
        current_vat = (current_amount_ht * vat_ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        current_ttc = current_amount_ht + current_vat
        
        # Calculate retention on current amount
        retention_amount = Decimal('0')
        if retention_rate and retention_rate > 0:
            retention = Decimal(str(retention_rate)) / 100
            retention_amount = (current_ttc * retention).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        net_current = current_ttc - retention_amount
        
        return {
            "full_contract_ht": full_totals["subtotal_after_discount"],
            "full_contract_ttc": full_totals["total_ttc"],
            "progress_percentage": progress_percentage,
            "cumulative_to_date_ht": float(total_to_date_ht),
            "previous_invoiced_ht": previous_invoiced,
            "current_amount_ht": float(current_amount_ht),
            "current_vat": float(current_vat),
            "current_ttc": float(current_ttc),
            "retention_rate": retention_rate,
            "retention_amount": float(retention_amount),
            "net_to_pay": float(net_current),
            "remaining_ht": float(Decimal(str(full_totals["subtotal_after_discount"])) - total_to_date_ht)
        }
    
    @staticmethod
    def get_applicable_rate(work_type: str, building_age_years: int = None, 
                            is_energy_improvement: bool = False) -> Dict[str, Any]:
        """Determine applicable VAT rate based on BTP rules"""
        if is_energy_improvement and building_age_years and building_age_years >= 2:
            return {
                "rate": 5.5,
                "rule": "energy_improvement",
                "description": "Travaux d'amélioration énergétique sur bâtiment de plus de 2 ans"
            }
        
        if building_age_years is not None:
            if building_age_years < 2:
                return {
                    "rate": 20.0,
                    "rule": "renovation_recent",
                    "description": "Bâtiment de moins de 2 ans - TVA normale"
                }
            else:
                return {
                    "rate": 10.0,
                    "rule": "renovation_old",
                    "description": "Rénovation d'un bâtiment de plus de 2 ans"
                }
        
        if work_type in ["new_construction", "extension"]:
            return {
                "rate": 20.0,
                "rule": "new_construction",
                "description": "Construction neuve ou extension"
            }
        
        # Default to standard rate
        return {
            "rate": 20.0,
            "rule": "standard",
            "description": "Taux normal"
        }
    
    @staticmethod
    def get_all_rates() -> Dict[str, float]:
        """Get all available VAT rates"""
        return VAT_RATES.copy()
    
    @staticmethod
    def get_vat_rules() -> Dict[str, Dict]:
        """Get VAT applicability rules"""
        return VAT_RULES.copy()


# Create singleton instance
vat_service = VATService()
