import frappe
from frappe.utils import flt, rounded
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        """Override validate method to fix VAT precision issues before ZATCA validation"""
        self.fix_zatca_precision()
        super().validate()
    
    def before_submit(self):
        """Fix precision issues before submit"""
        self.fix_zatca_precision()
        super().before_submit() if hasattr(super(), 'before_submit') else None
    
    def on_submit(self):
        """Override on_submit to fix precision before ZATCA compliance kicks in"""
        self.fix_zatca_precision()
        
        # Force reload to ensure changes are persisted
        self.reload()
        
        super().on_submit()
    
    def fix_zatca_precision(self):
        """Fix VAT precision for ZATCA compliance"""
        
        if not self.items:
            return
        
        try:
            # Step 1: Fix item amounts
            net_total = 0
            for item in self.items:
                if item.amount:
                    item.amount = flt(item.amount, 2)
                    net_total += item.amount
            
            self.net_total = flt(net_total, 2)
            
            # Step 2: Fix VAT calculation for exact ZATCA compliance
            if self.taxes:
                vat_tax = None
                vat_rate = 0
                
                # Find VAT tax row
                for tax in self.taxes:
                    if (tax.account_head and 
                        ('VAT' in str(tax.account_head).upper() or 
                         'Tax' in str(tax.account_head) or
                         tax.rate == 15)):
                        vat_tax = tax
                        vat_rate = tax.rate or 15
                        break
                
                if vat_tax:
                    # Calculate exact VAT for ZATCA BR-CO-14
                    calculated_vat = flt((self.net_total * vat_rate) / 100, 2)
                    vat_tax.tax_amount = calculated_vat
                    
                    # Recalculate totals
                    total_taxes = sum(flt(tax.tax_amount, 2) for tax in self.taxes if tax.tax_amount)
                    
                    self.total_taxes_and_charges = flt(total_taxes, 2)
                    self.grand_total = flt(self.net_total + self.total_taxes_and_charges, 2)
                    self.outstanding_amount = flt(self.grand_total, 2)
                    
                    # Fix base currency
                    if self.conversion_rate and self.conversion_rate != 1:
                        self.base_net_total = flt(self.net_total * self.conversion_rate, 2)
                        self.base_total_taxes_and_charges = flt(self.total_taxes_and_charges * self.conversion_rate, 2)
                        self.base_grand_total = flt(self.grand_total * self.conversion_rate, 2)
                        self.base_outstanding_amount = flt(self.outstanding_amount * self.conversion_rate, 2)
            
            # Force update the database immediately
            frappe.db.sql("""
                UPDATE `tabSales Invoice` 
                SET net_total=%s, total_taxes_and_charges=%s, grand_total=%s, outstanding_amount=%s
                WHERE name=%s
            """, (self.net_total, self.total_taxes_and_charges, self.grand_total, self.outstanding_amount, self.name))
            
            if self.taxes and vat_tax:
                frappe.db.sql("""
                    UPDATE `tabSales Taxes and Charges` 
                    SET tax_amount=%s 
                    WHERE parent=%s AND account_head=%s
                """, (vat_tax.tax_amount, self.name, vat_tax.account_head))
            
            frappe.db.commit()
            
            frappe.logger().info(f"ZATCA precision fixed and committed: {self.name}")
            
        except Exception as e:
            frappe.logger().error(f"Error in ZATCA precision fix: {str(e)}")
            pass