import frappe
from frappe.utils import flt, rounded
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        """Override validate method to fix VAT precision issues before ZATCA validation"""
        self.fix_all_precision_issues()
        super().validate()
    
    def before_submit(self):
        """Fix precision issues before submit"""
        self.fix_all_precision_issues()
        super().before_submit() if hasattr(super(), 'before_submit') else None
    
    def on_submit(self):
        """Override on_submit to handle both ZATCA and GL entry issues"""
        
        # Fix precision issues one final time
        self.fix_all_precision_issues()
        
        try:
            # Call parent on_submit
            super().on_submit()
        except frappe.ValidationError as e:
            if "Debit and Credit not equal" in str(e):
                frappe.logger().info(f"GL entry error for {self.name}, attempting comprehensive fix...")
                
                # Delete any existing GL entries
                frappe.db.sql("""DELETE FROM `tabGL Entry` WHERE voucher_type = %s AND voucher_no = %s""", 
                             (self.doctype, self.name))
                
                # Apply more aggressive precision fix
                self.fix_all_precision_issues(aggressive=True)
                
                # Retry submission
                super().on_submit()
            else:
                raise
    
    def fix_all_precision_issues(self, aggressive=False):
        """Comprehensive fix for all precision issues affecting ZATCA and GL entries"""
        
        if not self.items:
            return
        
        try:
            # Step 1: Fix item-level precision
            net_total = 0
            for item in self.items:
                # Fix item rates and amounts
                if item.rate:
                    item.rate = flt(item.rate, 2)
                if item.qty:
                    item.qty = flt(item.qty, 3)
                
                # Recalculate amount
                if item.rate and item.qty:
                    item.amount = flt(item.rate * item.qty, 2)
                elif item.amount:
                    item.amount = flt(item.amount, 2)
                
                if item.amount:
                    net_total += item.amount
                
                # Fix base currency items
                if self.conversion_rate and self.conversion_rate != 1:
                    if hasattr(item, 'base_rate'):
                        item.base_rate = flt(item.rate * self.conversion_rate, 2)
                    if hasattr(item, 'base_amount'):
                        item.base_amount = flt(item.amount * self.conversion_rate, 2)
                    if hasattr(item, 'base_net_rate'):
                        item.base_net_rate = item.base_rate
                    if hasattr(item, 'base_net_amount'):
                        item.base_net_amount = item.base_amount
            
            # Step 2: Set net total
            self.net_total = flt(net_total, 2)
            
            # Step 3: Fix tax calculations for ZATCA compliance
            total_taxes = 0
            running_total = self.net_total
            
            if self.taxes:
                for tax in self.taxes:
                    # Calculate tax amount based on charge type
                    if tax.charge_type == "On Net Total" and tax.rate:
                        tax.tax_amount = flt((self.net_total * tax.rate) / 100, 2)
                    elif tax.charge_type == "On Previous Row Total" and tax.rate:
                        tax.tax_amount = flt((running_total * tax.rate) / 100, 2)
                    elif tax.tax_amount:
                        tax.tax_amount = flt(tax.tax_amount, 2)
                    
                    # Update running total
                    if tax.tax_amount:
                        total_taxes += tax.tax_amount
                        running_total += tax.tax_amount
                    
                    # Set cumulative total for this tax row
                    tax.total = flt(running_total, 2)
                    
                    # Fix base tax amounts
                    if self.conversion_rate and self.conversion_rate != 1:
                        if hasattr(tax, 'base_tax_amount'):
                            tax.base_tax_amount = flt(tax.tax_amount * self.conversion_rate, 2)
                        if hasattr(tax, 'base_total'):
                            tax.base_total = flt(tax.total * self.conversion_rate, 2)
            
            # Step 4: Set document totals
            self.total_taxes_and_charges = flt(total_taxes, 2)
            self.grand_total = flt(self.net_total + self.total_taxes_and_charges, 2)
            self.outstanding_amount = flt(self.grand_total, 2)
            
            # Step 5: Handle rounding
            if hasattr(self, 'rounded_total'):
                self.rounded_total = flt(round(self.grand_total), 2)
            
            # Step 6: Fix base currency totals
            if self.conversion_rate and self.conversion_rate != 1:
                conversion_rate = flt(self.conversion_rate, 6)
                self.base_net_total = flt(self.net_total * conversion_rate, 2)
                self.base_total_taxes_and_charges = flt(self.total_taxes_and_charges * conversion_rate, 2)
                self.base_grand_total = flt(self.grand_total * conversion_rate, 2)
                self.base_outstanding_amount = flt(self.outstanding_amount * conversion_rate, 2)
                
                if hasattr(self, 'base_rounded_total'):
                    self.base_rounded_total = flt(round(self.base_grand_total), 2)
            
            # Step 7: Fix additional fields that affect GL entries
            precision_fields = [
                'discount_amount', 'write_off_amount', 'paid_amount', 
                'change_amount', 'total_advance', 'allocated_amount'
            ]
            
            for field in precision_fields:
                if hasattr(self, field) and getattr(self, field):
                    setattr(self, field, flt(getattr(self, field), 2))
                    
                    # Fix base currency equivalent
                    base_field = f'base_{field}'
                    if (hasattr(self, base_field) and self.conversion_rate and 
                        self.conversion_rate != 1):
                        setattr(self, base_field, 
                               flt(getattr(self, field) * self.conversion_rate, 2))
            
            # Step 8: Fix payment schedule
            if hasattr(self, 'payment_schedule') and self.payment_schedule:
                total_scheduled = 0
                for payment in self.payment_schedule:
                    if payment.payment_amount:
                        payment.payment_amount = flt(payment.payment_amount, 2)
                        total_scheduled += payment.payment_amount
                
                # Adjust for any rounding differences
                if abs(total_scheduled - self.grand_total) > 0.01:
                    adjustment = flt(self.grand_total - total_scheduled, 2)
                    if self.payment_schedule:
                        self.payment_schedule[-1].payment_amount = flt(
                            self.payment_schedule[-1].payment_amount + adjustment, 2)
            
            # Step 9: Fix advance allocations
            if hasattr(self, 'advances') and self.advances:
                for advance in self.advances:
                    if advance.allocated_amount:
                        advance.allocated_amount = flt(advance.allocated_amount, 2)
            
            # Step 10: Aggressive mode - direct database updates
            if aggressive and self.name:
                frappe.db.sql("""
                    UPDATE `tabSales Invoice` 
                    SET net_total=%s, total_taxes_and_charges=%s, grand_total=%s, 
                        outstanding_amount=%s, base_net_total=%s, base_total_taxes_and_charges=%s,
                        base_grand_total=%s, base_outstanding_amount=%s
                    WHERE name=%s
                """, (
                    self.net_total, self.total_taxes_and_charges, self.grand_total, 
                    self.outstanding_amount, getattr(self, 'base_net_total', 0),
                    getattr(self, 'base_total_taxes_and_charges', 0),
                    getattr(self, 'base_grand_total', 0), 
                    getattr(self, 'base_outstanding_amount', 0), self.name
                ))
                
                # Update tax amounts in database
                if self.taxes:
                    for tax in self.taxes:
                        frappe.db.sql("""
                            UPDATE `tabSales Taxes and Charges`
                            SET tax_amount=%s, total=%s, base_tax_amount=%s, base_total=%s
                            WHERE name=%s
                        """, (
                            tax.tax_amount, tax.total,
                            getattr(tax, 'base_tax_amount', 0),
                            getattr(tax, 'base_total', 0), tax.name
                        ))
                
                frappe.db.commit()
            
            frappe.logger().info(
                f"Precision fix applied ({'aggressive' if aggressive else 'normal'}): "
                f"Invoice {self.name}, Net={self.net_total}, Tax={self.total_taxes_and_charges}, "
                f"Grand={self.grand_total}"
            )
            
        except Exception as e:
            frappe.logger().error(f"Error in precision fix: {str(e)}")
            frappe.log_error(f"Precision Fix Error for {self.name}: {str(e)}")
            pass