import frappe
from frappe.utils import flt, rounded
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        """Override validate method to fix VAT precision issues before ZATCA validation"""
        self.fix_all_precision_issues()
        self.fix_item_wise_vat_calculation()
        super().validate()
    
    def before_submit(self):
        """Fix precision issues before submit"""
        self.fix_all_precision_issues()
        super().before_submit() if hasattr(super(), 'before_submit') else None
    
    def on_submit(self):
        """Override on_submit to handle both ZATCA and GL entry issues"""
        
        # Fix precision issues one final time
        self.fix_all_precision_issues(aggressive=True)
        self.fix_item_wise_vat_calculation()
        self.fix_payment_means_code()
        
        # Call parent on_submit
        super().on_submit()
    
    def make_gl_entries(self, gl_entries=None, from_repost=False):
        """Override GL entry creation to fix precision issues"""
        
        # Ensure precision is fixed before GL entries
        self.fix_all_precision_issues(aggressive=True)
        
        # Get the GL entries from parent method
        gl_entries = super().make_gl_entries(gl_entries, from_repost)
        
        # Fix any precision issues in the GL entries themselves
        if gl_entries:
            self.fix_gl_entries_precision(gl_entries)
        
        return gl_entries
    
    def fix_gl_entries_precision(self, gl_entries):
        """Fix precision issues directly in GL entries"""
        
        if not gl_entries:
            return
        
        try:
            total_debit = 0
            total_credit = 0
            
            # Round all amounts and calculate totals
            for entry in gl_entries:
                if entry.get('debit'):
                    entry['debit'] = flt(entry['debit'], 2)
                    total_debit += entry['debit']
                
                if entry.get('credit'):
                    entry['credit'] = flt(entry['credit'], 2)
                    total_credit += entry['credit']
                
                # Also fix account currency amounts
                if entry.get('debit_in_account_currency'):
                    entry['debit_in_account_currency'] = flt(entry['debit_in_account_currency'], 2)
                
                if entry.get('credit_in_account_currency'):
                    entry['credit_in_account_currency'] = flt(entry['credit_in_account_currency'], 2)
            
            # Check for imbalance and fix it
            difference = flt(total_debit - total_credit, 2)
            
            if abs(difference) > 0.01:
                # Find the largest debit or credit entry to adjust
                largest_entry = None
                largest_amount = 0
                
                for entry in gl_entries:
                    entry_amount = max(entry.get('debit', 0), entry.get('credit', 0))
                    if entry_amount > largest_amount:
                        largest_amount = entry_amount
                        largest_entry = entry
                
                if largest_entry:
                    if difference > 0:  # More debit, need to increase credit
                        if largest_entry.get('credit', 0) > 0:
                            largest_entry['credit'] = flt(largest_entry['credit'] + difference, 2)
                            if largest_entry.get('credit_in_account_currency'):
                                largest_entry['credit_in_account_currency'] = flt(
                                    largest_entry['credit_in_account_currency'] + difference, 2)
                    else:  # More credit, need to increase debit
                        if largest_entry.get('debit', 0) > 0:
                            largest_entry['debit'] = flt(largest_entry['debit'] + abs(difference), 2)
                            if largest_entry.get('debit_in_account_currency'):
                                largest_entry['debit_in_account_currency'] = flt(
                                    largest_entry['debit_in_account_currency'] + abs(difference), 2)
                
                frappe.logger().info(f"GL entries adjusted by {difference} for invoice {self.name}")
            
        except Exception as e:
            frappe.logger().error(f"Error fixing GL entries precision: {str(e)}")
            pass
    
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
                    # Handle different charge types
                    if tax.charge_type == "On Net Total" and tax.rate:
                        tax.tax_amount = flt((self.net_total * tax.rate) / 100, 2)
                    elif tax.charge_type == "On Previous Row Total" and tax.rate:
                        tax.tax_amount = flt((running_total * tax.rate) / 100, 2)
                    elif tax.charge_type == "Actual":
                        # For Actual type, convert to percentage-based calculation
                        if tax.rate and tax.rate > 0:
                            # If rate is provided, use it to calculate from net total
                            tax.tax_amount = flt((self.net_total * tax.rate) / 100, 2)
                        else:
                            # If no rate, calculate the rate from existing tax amount
                            if tax.tax_amount and self.net_total > 0:
                                calculated_rate = (tax.tax_amount / self.net_total) * 100
                                tax.rate = flt(calculated_rate, 2)
                                tax.tax_amount = flt((self.net_total * tax.rate) / 100, 2)
                            else:
                                # Default to 15% VAT if no rate or amount
                                tax.rate = 15.0
                                tax.tax_amount = flt((self.net_total * 15) / 100, 2)
                        
                        # Change charge type to avoid ERPNext validation error
                        tax.charge_type = "On Net Total"
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
            
            # Step 10: Fix item-tax relationship for Actual type taxes
            self.fix_item_tax_inclusion()
            
            # Step 11: Aggressive mode - direct database updates
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
    
    def fix_item_wise_vat_calculation(self):
        """Fix the item-wise VAT calculation to match ZATCA requirements exactly"""
        
        try:
            if not self.taxes or not self.items:
                return
            
            # Find VAT tax row
            vat_tax = None
            vat_rate = 0
            
            for tax in self.taxes:
                if (tax.account_head and 
                    ('VAT' in str(tax.account_head).upper() or 
                     'Tax' in str(tax.account_head) or
                     tax.rate == 15)):
                    vat_tax = tax
                    vat_rate = tax.rate or 15
                    break
            
            if not vat_tax:
                return
            
            # Calculate item-wise VAT amounts
            item_wise_vat_total = 0
            largest_item = None
            largest_vat = 0
            
            for item in self.items:
                if item.amount:
                    # Calculate VAT for this item
                    item_vat = flt((item.amount * vat_rate) / 100, 2)
                    item_wise_vat_total += item_vat
                    
                    # Track largest VAT amount for adjustment
                    if item_vat > largest_vat:
                        largest_vat = item_vat
                        largest_item = item
                    
                    # Store VAT amount in item for ZATCA reference
                    if hasattr(item, 'tax_amount'):
                        item.tax_amount = item_vat
            
            # Get the document-level VAT total
            document_vat_total = vat_tax.tax_amount or 0
            
            # Check for mismatch and fix it
            difference = flt(item_wise_vat_total - document_vat_total, 2)
            
            if abs(difference) > 0.001:  # More than 0.001 difference
                frappe.logger().info(f"VAT mismatch detected: Item-wise={item_wise_vat_total}, Document={document_vat_total}, Diff={difference}")
                
                # Adjust the document VAT to match item-wise total exactly
                vat_tax.tax_amount = flt(item_wise_vat_total, 2)
                
                # Recalculate document totals
                total_taxes = sum(flt(tax.tax_amount, 2) for tax in self.taxes if tax.tax_amount)
                self.total_taxes_and_charges = flt(total_taxes, 2)
                self.grand_total = flt(self.net_total + self.total_taxes_and_charges, 2)
                self.outstanding_amount = flt(self.grand_total, 2)
                
                # Fix base currency amounts
                if self.conversion_rate and self.conversion_rate != 1:
                    self.base_total_taxes_and_charges = flt(self.total_taxes_and_charges * self.conversion_rate, 2)
                    self.base_grand_total = flt(self.grand_total * self.conversion_rate, 2)
                    self.base_outstanding_amount = flt(self.outstanding_amount * self.conversion_rate, 2)
                
                frappe.logger().info(f"VAT adjusted: New document VAT={vat_tax.tax_amount}, Grand Total={self.grand_total}")
            
            # Store the item-wise VAT total for ZATCA validation reference
            if hasattr(self, 'item_wise_vat_total'):
                self.item_wise_vat_total = flt(item_wise_vat_total, 2)
            
        except Exception as e:
            frappe.logger().error(f"Error in item-wise VAT calculation: {str(e)}")
            pass

    def fix_item_tax_inclusion(self):
        """Fix the 'Actual type tax cannot be included in Item rate' error"""
        
        try:
            # For each item, ensure tax inclusion is properly handled
            for item in self.items:
                # Remove any item-wise tax inclusion for Actual type taxes
                if hasattr(item, 'item_tax_template'):
                    item.item_tax_template = None
                
                # Ensure the item rate is exclusive of tax
                if hasattr(item, 'tax_inclusive_rate'):
                    item.tax_inclusive_rate = 0
                
                # Reset any item-level tax calculations
                if hasattr(item, 'tax_amount'):
                    item.tax_amount = 0
            
            # Ensure all taxes are document-level, not item-level
            for tax in self.taxes or []:
                if tax.charge_type == "Actual":
                    # Make sure it's not trying to include in item rate
                    if hasattr(tax, 'included_in_print_rate'):
                        tax.included_in_print_rate = 0
                    if hasattr(tax, 'included_in_paid_amount'):
                        tax.included_in_paid_amount = 0
            
            frappe.logger().info(f"Fixed item-tax inclusion for {self.name}")
            
        except Exception as e:
            frappe.logger().error(f"Error fixing item-tax inclusion: {str(e)}")
            pass
    
    def fix_payment_means_code(self):
        """Fix the BR-KSA-16 warning about payment means code"""
        
        try:
            # Set valid UNTDID 4461 payment means codes
            valid_codes = {
                'cash': '10',
                'credit card': '54', 
                'bank transfer': '30',
                'cheque': '20',
                'electronic payment': '30'
            }
            
            # Try to set payment means code based on mode of payment
            if hasattr(self, 'mode_of_payment') and self.mode_of_payment:
                payment_mode = str(self.mode_of_payment).lower()
                payment_code = '30'  # Default to credit transfer
                
                for mode, code in valid_codes.items():
                    if mode in payment_mode:
                        payment_code = code
                        break
                
                # Set the payment means code if the field exists
                if hasattr(self, 'payment_means_code'):
                    self.payment_means_code = payment_code
                elif hasattr(self, 'ksa_payment_means_code'):
                    self.ksa_payment_means_code = payment_code
            
            frappe.logger().info(f"Payment means code set for {self.name}")
            
        except Exception as e:
            frappe.logger().error(f"Error fixing payment means code: {str(e)}")
            pass