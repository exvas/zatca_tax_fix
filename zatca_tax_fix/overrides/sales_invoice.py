import frappe
from frappe.utils import flt, rounded
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        """Override validate method to fix VAT precision issues before ZATCA validation"""
        
        # Fix VAT precision issues BEFORE standard validation
        self.fix_zatca_vat_precision()
        
        # Call parent validation (includes ZATCA validation)
        super().validate()
    
    def fix_zatca_vat_precision(self):
        """Fix VAT precision issues for ZATCA compliance"""
        
        if not self.taxes or not self.items:
            return
        
        try:
            # Step 1: Fix item amounts with proper precision
            net_total = 0
            for item in self.items:
                if item.amount:
                    # Round item amount to 2 decimal places
                    item.amount = flt(item.amount, 2)
                    net_total += item.amount
            
            # Step 2: Set net total with proper precision
            self.net_total = flt(net_total, 2)
            
            # Step 3: Fix tax calculations
            total_taxes = 0
            
            for tax in self.taxes:
                if tax.charge_type == "On Net Total" and tax.rate:
                    # Calculate tax amount with exact precision
                    calculated_tax = (self.net_total * tax.rate) / 100
                    tax.tax_amount = flt(calculated_tax, 2)
                    total_taxes += tax.tax_amount
                
                elif tax.charge_type == "Actual" and tax.tax_amount:
                    # For actual tax amounts, just ensure proper rounding
                    tax.tax_amount = flt(tax.tax_amount, 2)
                    total_taxes += tax.tax_amount
            
            # Step 4: Update document totals with exact precision
            self.total_taxes_and_charges = flt(total_taxes, 2)
            self.grand_total = flt(self.net_total + self.total_taxes_and_charges, 2)
            self.rounded_total = rounded(self.grand_total)
            
            # Step 5: Fix base currency amounts if needed
            if hasattr(self, 'base_net_total') and self.conversion_rate:
                conversion_rate = flt(self.conversion_rate, 6)
                self.base_net_total = flt(self.net_total * conversion_rate, 2)
                self.base_total_taxes_and_charges = flt(self.total_taxes_and_charges * conversion_rate, 2)
                self.base_grand_total = flt(self.grand_total * conversion_rate, 2)
                self.base_rounded_total = rounded(self.base_grand_total)
            
            # Log the fix for debugging
            frappe.logger().info(
                f"ZATCA VAT Fix Applied - Sales Invoice: {self.name or 'New'}, "
                f"Net: {self.net_total}, Tax: {self.total_taxes_and_charges}, "
                f"Grand: {self.grand_total}"
            )
            
        except Exception as e:
            frappe.logger().error(f"Error in ZATCA VAT precision fix: {str(e)}")
            pass