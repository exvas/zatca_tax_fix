import frappe
from frappe.utils import flt, rounded


def before_validate(doc, method):
    """Event handler for Sales Invoice before_validate"""
    fix_vat_precision(doc)


def before_save(doc, method):
    """Event handler for Sales Invoice before_save"""
    fix_vat_precision(doc)


def validate(doc, method):
    """Event handler for Sales Invoice validate"""
    fix_vat_precision(doc)


def fix_vat_precision(doc):
    """Fix VAT precision issues for ZATCA compliance"""
    
    if not doc.taxes or not doc.items:
        return
    
    try:
        # Calculate precise net total
        net_total = 0
        for item in doc.items:
            if item.amount:
                item.amount = flt(item.amount, 2)
                net_total += item.amount
        
        # Set net total with proper precision
        doc.net_total = flt(net_total, 2)
        
        # Fix tax calculations
        total_taxes = 0
        
        for tax in doc.taxes:
            if tax.charge_type == "On Net Total" and tax.rate:
                calculated_tax = (doc.net_total * tax.rate) / 100
                tax.tax_amount = flt(calculated_tax, 2)
                total_taxes += tax.tax_amount
            elif tax.charge_type == "Actual" and tax.tax_amount:
                tax.tax_amount = flt(tax.tax_amount, 2)
                total_taxes += tax.tax_amount
        
        # Update document totals
        doc.total_taxes_and_charges = flt(total_taxes, 2)
        doc.grand_total = flt(doc.net_total + doc.total_taxes_and_charges, 2)
        doc.rounded_total = rounded(doc.grand_total)
        
        # Fix base currency amounts if needed
        if hasattr(doc, 'base_net_total') and doc.conversion_rate:
            conversion_rate = flt(doc.conversion_rate, 6)
            doc.base_net_total = flt(doc.net_total * conversion_rate, 2)
            doc.base_total_taxes_and_charges = flt(doc.total_taxes_and_charges * conversion_rate, 2)
            doc.base_grand_total = flt(doc.grand_total * conversion_rate, 2)
            doc.base_rounded_total = rounded(doc.base_grand_total)
            
    except Exception as e:
        frappe.logger().error(f"Error in VAT precision fix: {str(e)}")
        pass