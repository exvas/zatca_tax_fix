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


def before_submit(doc, method):
    """Event handler for Sales Invoice before_submit - Fix GL entry issues"""
    fix_vat_precision(doc)
    fix_gl_precision(doc)


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
def fix_gl_precision(doc):
    """Fix GL entry precision issues"""
    
    try:
        # Ensure all amounts that will be used in GL entries are properly rounded
        if hasattr(doc, 'outstanding_amount'):
            doc.outstanding_amount = flt(doc.grand_total, 2)
        
        if hasattr(doc, 'base_outstanding_amount') and doc.conversion_rate:
            doc.base_outstanding_amount = flt(doc.outstanding_amount * doc.conversion_rate, 2)
        
        # Fix advance payments amounts if any
        if hasattr(doc, 'advances') and doc.advances:
            for advance in doc.advances:
                if advance.allocated_amount:
                    advance.allocated_amount = flt(advance.allocated_amount, 2)
        
        # Ensure tax totals match for GL entries
        if doc.taxes:
            recalculated_tax_total = 0
            for tax in doc.taxes:
                if tax.tax_amount:
                    tax.tax_amount = flt(tax.tax_amount, 2)
                    recalculated_tax_total += tax.tax_amount
            
            # Ensure the total matches
            doc.total_taxes_and_charges = flt(recalculated_tax_total, 2)
            doc.grand_total = flt(doc.net_total + doc.total_taxes_and_charges, 2)
        
        frappe.logger().info(f"GL precision fix applied for {doc.name or 'New'}")
        
    except Exception as e:
        frappe.logger().error(f"Error in GL precision fix: {str(e)}")
        pass