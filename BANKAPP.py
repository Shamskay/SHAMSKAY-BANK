from BANKCONFIG import (BANKCONFIG, money_format, email_validate, validate_password, speak)


class BANKAPP(BANKCONFIG):
    def __init__(self, bank_name):
        super().__init__()
        self.bank_name = bank_name
        self.Home()

    def Home(self):
        while True:
            speak(f"Welcome to {self.bank_name}.")
            print(f"\n{'=' * 30}")
            print(f"   WELCOME TO {self.bank_name}")
            print(f"{'=' * 30}")
            print("""
            ======= WHAT CAN WE DO FOR YOU TODAY? =======
            
            1. Register
            2. Login
            3. Forgot Password
            4. Admin Login
            5. Exit
            """)
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.Register()
            elif choice == "2":
                self.Login()
            elif choice == "3":
                self.ForgotPassword()
            elif choice == "4":
                self.AdminLogin()
            elif choice == "5":
                speak(f"Thank you for banking with us at {self.bank_name}.")
                print("Goodbye!")
                exit()
            else:
                print("Invalid choice. Please try again.")

    def Register(self):
        print("\n===== REGISTER =====")
        full_name = input("Full Name: ").strip()
        email = input("Email: ").strip()
        phone_number = input("Phone Number: ").strip()
        address = input("Address: ").strip()
        date_of_birth = input("Date of Birth (YYYY-MM-DD): ").strip()
        gender = input("Gender (Male/Female): ").strip()
        password = input("Password: ").strip()
        confirm_password = input("Confirm Password: ").strip()

        if not full_name:
            print("Full name is required.")
            return
        if not email:
            print("Email is required.")
            return
        if not phone_number:
            print("Phone number is required.")
            return
        if len(phone_number) > 11:
            print("Phone number must not exceed 11 digits.")
            return
        if self.get_customer_by_phone(phone_number):
            print("This phone number is already registered. Please use another phone number.")
            return
        if not address:
            print("Address is required.")
            return
        if not date_of_birth:
            print("Date of birth is required.")
            return
        if not gender:
            print("Gender is required.")
            return
        gender = gender.title()
        if gender not in ["Male", "Female"]:
            print("Gender must be Male or Female.")
            return
        if not email_validate(email):
            print("Invalid email format. Use the form name@gmail.com")
            return
        if not validate_password(password):
            print("Password must be at least 8 characters with uppercase, lowercase, number, and special character.")
            return
        if password != confirm_password:
            print("Passwords do not match.")
            return

        print("\nSending verification OTP to your email...")
        if not self.send_email_otp(email):
            print("Failed to send OTP. Please try again.")
            return

        otp_attempts = 0
        while otp_attempts < 3:
            otp = input("Enter OTP sent to your email (or type 'resend' to get a new one): ").strip()
            if otp.lower() == "resend":
                print("Resending OTP...")
                if not self.send_email_otp(email):
                    print("Failed to resend OTP. Please try again.")
                    return
                continue

            if self.verify_email_otp(email, otp):
                result = self.create_customer(full_name, email, password, confirm_password, phone_number=phone_number, address=address, date_of_birth=date_of_birth, gender=gender, otp_verified=True)
                if result["status"]:
                    customer = result["data"]
                    print("\nRegistration successful!")
                    print(f"Account Number: {customer['account_number']}")
                    print("Please keep your account number safe.")
                else:
                    print(f"Registration failed: {result['message']}")
                return
            else:
                otp_attempts += 1
                if otp_attempts < 3:
                    print(f"Invalid or expired OTP. {3 - otp_attempts} attempts remaining.")
                else:
                    print("Invalid or expired OTP. Maximum attempts reached. Please start registration again.")
        print(f"Now you can login into your account.")
        self.Login()


    def Login(self):
        print("\n===== LOGIN =====")
        email = input("Email: ").strip()
        password = input("Password: ").strip()

        result = self.login_customer(email, password)
        if not result["status"]:
            print(result["message"])
            if result["message"] == "Incorrect password.":
                print("Forgot your password? Choose 'Forgot Password' from the home menu.")
            return
        
        customer = result["data"]
        print(result["message"])
        self.dashboard(customer)
        

    def ForgotPassword(self):
        print("\n===== FORGOT PASSWORD =====")
        email = input("Email: ").strip()

        if not email_validate(email):
            print("Invalid email format. Use the form name@gmail.com")
            return

        print("Sending password reset OTP to your email...")
        otp_request = self.send_forgot_password_otp(email)
        if not otp_request["status"]:
            print(otp_request["message"])
            return

        otp_attempts = 0
        while otp_attempts < 3:
            otp = input("Enter OTP sent to your email (or type 'resend' to get a new one): ").strip()
            if otp.lower() == "resend":
                print("Resending password reset OTP...")
                otp_request = self.send_forgot_password_otp(email)
                print(otp_request["message"])
                continue

            new_password = input("New Password: ").strip()
            confirm_password = input("Confirm New Password: ").strip()

            if not validate_password(new_password):
                print("Password must be at least 8 characters with uppercase, lowercase, number, and special character.")
                continue
            if new_password != confirm_password:
                print("Passwords do not match.")
                continue

            result = self.reset_forgot_password(email, new_password, confirm_password, otp)
            print(result["message"])
            if result["status"]:
                return

            otp_attempts += 1
            if otp_attempts < 3:
                print(f"Incorrect or expired OTP. {3 - otp_attempts} attempts remaining.")
            else:
                print("Incorrect or expired OTP. Maximum attempts reached. Please request a new password reset OTP.")

    def AdminLogin(self):
        print("\n===== ADMIN LOGIN =====")
        password = input("Admin Password: ").strip()
        result = self.admin_login(password)
        if not result["status"]:
            print(result["message"])
            return
        print(result["message"])
        self.admin_dashboard()

    def admin_dashboard(self):
        while True:
            print("""
            ===== ADMIN DASHBOARD =====
            1. View All Customers
            2. View Customer Transactions
            3. Freeze Account
            4. Unfreeze Account
            5. Logout
            """)
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.view_all_customers()
            elif choice == "2":
                self.view_customer_transactions()
            elif choice == "3":
                self.freeze_account()
            elif choice == "4":
                self.unfreeze_account()
            elif choice == "5":
                print("Admin logged out successfully.")
                return
            else:
                print("Invalid choice. Please try again.")

    def view_all_customers(self):
        print("\n===== ALL CUSTOMERS =====")
        result = self.get_all_customers()
        if not result["status"]:
            print(result["message"])
            return

        print(f"\n{'Account No':<14} {'Name':<20} {'Email':<25} {'Balance':<15} {'Frozen'}")
        print("-" * 90)
        for c in result["data"]:
            frozen = "Yes" if c.get("is_frozen") else "No"
            print(f"{c['account_number']:<14} {c['full_name'][:20]:<20} {c['email']:<25} {money_format(c['balance']):<15} {frozen}")

    def view_customer_transactions(self):
        print("\n===== VIEW CUSTOMER TRANSACTIONS =====")
        account_number = input("Customer Account Number: ").strip()
        result = self.view_transactions(account_number)

        if not result["status"]:
            print(result["message"])
            return

        customer = self.get_customer_by_account(account_number)
        if customer:
            print(f"\nTransactions for: {customer['full_name']} ({account_number})")
        else:
            print(f"\nTransactions for account: {account_number}")

        print(f"\n{'Date':<22} {'Type':<18} {'Amount':<14} {'Balance After':<14} {'Reference'}")
        print("-" * 95)
        for transaction in result["data"]:
            print(
                f"{str(transaction['created_at']):<22} "
                f"{transaction['transaction_type']:<18} "
                f"{money_format(transaction['amount']):<14} "
                f"{money_format(transaction['balance_after']):<14} "
                f"{transaction['reference']}"
            )

    def freeze_account(self):
        print("\n===== FREEZE ACCOUNT =====")
        account_number = input("Account Number to Freeze: ").strip()
        customer = self.get_customer_by_account(account_number)
        if not customer:
            print("Account not found.")
            return
        if customer.get("is_frozen"):
            print("Account is already frozen.")
            return
        result = self._freeze_account(account_number)
        print(result["message"])

    def unfreeze_account(self):
        print("\n===== UNFREEZE ACCOUNT =====")
        account_number = input("Account Number to Unfreeze: ").strip()
        customer = self.get_customer_by_account(account_number)
        if not customer:
            print("Account not found.")
            return
        if not customer.get("is_frozen"):
            print("Account is not frozen.")
            return
        result = self._unfreeze_account(account_number)
        print(result["message"])

    def dashboard(self, customer):
        while True:
            print(f"""
             ===== BANK DASHBOARD =====
             Hello, {customer['full_name']}
             Account Number: {customer['account_number']}
             1. View Balance
             2. Deposit Money
             3. Transfer Money
             4. Buy Airtime
             5. Pay Bills
             6. View Transaction History
             7. Create/Change Transaction PIN
             8. Change Password
             9. View Profile
             10. Edit Address
             11. Logout
             """)
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.view_balance_menu(customer)
            elif choice == "2":
                self.deposit_menu(customer)
            elif choice == "3":
                self.transfer_menu(customer)
            elif choice == "4":
                self.buy_airtime_menu(customer)
            elif choice == "5":
                self.pay_bill_menu(customer)
            elif choice == "6":
                self.transaction_history_menu(customer)
            elif choice == "7":
                self.manage_pin_menu(customer)
            elif choice == "8":
                self.change_password_menu(customer)
            elif choice == "9":
                self.profile_menu(customer)
            elif choice == "10":
                self.edit_address_menu(customer)
            elif choice == "11":
                print("Logged out successfully.")
                return
            else:
                print("Invalid choice. Please try again.")

    def refresh_customer(self, customer):
        updated = self.get_customer_by_account(customer["account_number"])
        if updated:
            customer.update(updated)

    def view_balance_menu(self, customer):
        self.refresh_customer(customer)
        result = self.view_balance(customer["account_number"])
        if result["status"]:
            print(f"\nAvailable Balance: {money_format(result['data']['balance'])}")
        else:
            print(result["message"])

    def deposit_menu(self, customer):
        print("\n===== DEPOSIT MONEY =====")
        amount = input("Amount: ").strip()
        result = self.deposit_money(customer["account_number"], amount)
        print(result["message"])
        if result["status"]:
            self.refresh_customer(customer)

    def buy_airtime_menu(self, customer):
        print("\n===== BUY AIRTIME =====")
        provider = input("Provider (MTN/Airtel/Glo/9mobile): ").strip()
        phone_number = input("Phone Number: ").strip()
        if not phone_number.isdigit() or len(phone_number) != 11:
            print("Airtime phone number must be exactly 11 digits.")
            return
        amount = input("Amount: ").strip()
        try:
            if float(amount) < 50:
                print("Minimum airtime purchase is NGN50.00.")
                return
        except Exception:
            print("Enter a valid amount.")
            return
        pin = input("Transaction PIN: ").strip()

        result = self.buy_airtime(customer["account_number"], pin, phone_number, amount, provider)
        print(result["message"])
        if result["status"]:
            self.refresh_customer(customer)
        self.dashboard(customer)

    def transfer_menu(self, customer):
        print("\n===== TRANSFER MONEY =====")
        recipient_account = input("Recipient Account Number: ").strip()
        recipient = self.get_customer_by_account(recipient_account)
        if not recipient:
            print("Recipient account not found.")
            return
        print(f"Recipient Name: {recipient['full_name']}")
        confirm = input("Do you want to proceed with this transfer? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Transfer cancelled.")
            return
        amount = input("Amount: ").strip()
        try:
            if float(amount) < 100:
                print("Minimum transfer amount is NGN100.00.")
                return
        except Exception:
            print("Enter a valid amount.")
            return
        pin = input("Transaction PIN: ").strip()

        result = self.transfer_money(customer["account_number"], recipient_account, pin, amount)
        if result["status"]:
            print(result["message"])
            print(f"Reference: {result['data']['reference']}")
            self.refresh_customer(customer)
        else:
            print(result["message"])

    def pay_bill_menu(self, customer):
        print("\n===== PAY BILLS =====")
        biller = input("Biller (Electricity/Internet/Cable/Other): ").strip()
        customer_id = input("Customer/Meter/Smart Card Number: ").strip()
        if not customer_id.isdigit() or len(customer_id) != 11:
            print("Biller smart card number must be exactly 11 digits.")
            return
        amount = input("Amount: ").strip()
        try:
            if float(amount) < 100:
                print("Minimum bill payment is NGN100.00.")
                return
        except Exception:
            print("Enter a valid amount.")
            return
        pin = input("Transaction PIN: ").strip()

        result = self.pay_bill(customer["account_number"], pin, biller, customer_id, amount)
        print(result["message"])
        if result["status"]:
            self.refresh_customer(customer)

    def transaction_history_menu(self, customer):
        print("\n===== TRANSACTION HISTORY =====")
        result = self.view_transactions(customer["account_number"])

        if not result["status"]:
            print(result["message"])
            return

        print(f"\n{'Date':<22} {'Type':<18} {'Amount':<14} {'Balance After':<14} {'Reference'}")
        print("-" * 95)
        for transaction in result["data"]:
            print(
                f"{str(transaction['created_at']):<22} "
                f"{transaction['transaction_type']:<18} "
                f"{money_format(transaction['amount']):<14} "
                f"{money_format(transaction['balance_after']):<14} "
                f"{transaction['reference']}"
            )

    def manage_pin_menu(self, customer):
        while True:
            print("""
            ===== TRANSACTION PIN =====
            1. Create PIN
            2. Change PIN
            3. Back
            """)
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                pin = input("Create 4-digit PIN: ").strip()
                verify_pin = input("Verify 4-digit PIN: ").strip()
                result = self.create_transaction_pin(customer["account_number"], pin, verify_pin)
                print(result["message"])
                if result["status"]:
                    return
            elif choice == "2":
                old_pin = input("Old PIN: ").strip()
                new_pin = input("New 4-digit PIN: ").strip()
                verify_pin = input("Verify New PIN: ").strip()
                result = self.change_transaction_pin(customer["account_number"], old_pin, new_pin, verify_pin)
                print(result["message"])
                if result["status"]:
                    otp = input("Enter the OTP sent to your email to verify PIN change: ").strip()
                    final = self._verify_and_apply(customer["account_number"], otp)
                    print(final["message"])
                    return
            elif choice == "3":
                return
            else:
                print("Invalid choice. Please try again.")

    def change_password_menu(self, customer):
        old_password = input("\nCurrent Password: ").strip()
        new_password = input("New Password: ").strip()
        confirm_password = input("Confirm New Password: ").strip()

        result = self.change_password(customer["account_number"], old_password, new_password, confirm_password)
        print(result["message"])
        if result["status"]:
            otp = input("Enter the OTP sent to your email to verify password change: ").strip()
            final = self._verify_and_apply(customer["account_number"], otp)
            print(final["message"])

    def profile_menu(self, customer):
        self.refresh_customer(customer)
        print("\n===== PROFILE =====")
        print(f"Full Name: {customer['full_name']}")
        print(f"Email: {customer['email']}")
        print(f"Phone: {customer.get('phone_number') or 'Not set'}")
        print(f"Address: {customer.get('address') or 'Not set'}")
        print(f"Date of Birth: {customer.get('date_of_birth') or 'Not set'}")
        print(f"Gender: {customer.get('gender') or 'Not set'}")
        print(f"Account Number: {customer['account_number']}")
        print(f"Balance: {money_format(customer['balance'])}")
        print(f"Account Created: {customer['created_at']}")
        input("\nPress Enter to go back...")

    def edit_address_menu(self, customer):
        self.refresh_customer(customer)
        print(f"\nCurrent Address: {customer.get('address') or 'Not set'}")
        new_address = input("Enter new address: ").strip()
        if not new_address:
            print("Address cannot be empty.")
            return
        result = self.update_address(customer["account_number"], new_address)
        print(result["message"])
        if result["status"]:
            self.refresh_customer(customer)


bank = BANKAPP("SHAMSKAY BANK")
