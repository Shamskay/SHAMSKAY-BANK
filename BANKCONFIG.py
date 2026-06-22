import hashlib
import re
import smtplib
import ssl
from datetime import datetime, timedelta
from decimal import Decimal
from email.mime.text import MIMEText

import mysql.connector as sql

BANK_DB = "SHAMSKAY_BANK"
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = ""
EMAIL_FROM = "shamskay@gmail.com"
EMAIL_PASSWORD = "juxeaagbvsyvwais"
SMTP_HOST = "smtp.gmail.com"


def speak(message):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        # If pyttsx3 is not installed, just skip speaking silently
        pass


def normalize_email(email):
    return email.strip().lower()


def email_validate(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))


def password_hash(plain_password):
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def password_check(plain_password, stored_hash):
    if not stored_hash:
        return False
    return password_hash(plain_password) == stored_hash


def pin_hash(plain_pin):
    return hashlib.sha256(plain_pin.encode("utf-8")).hexdigest()


def pin_check(plain_pin, stored_hash):
    if not stored_hash:
        return False
    return pin_hash(plain_pin) == stored_hash


def otp_hash(otp):
    return hashlib.sha256(str(otp).encode("utf-8")).hexdigest()


def validate_pin(pin):
    return bool(re.fullmatch(r"\d{4}", str(pin)))


def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\"<>,.?\|\/`~]", password):
        return False
    return True


def validate_amount(amount):
    try:
        value = Decimal(str(amount))
    except Exception:
        return None
    if value <= 0:
        return None
    return value.quantize(Decimal("0.01"))


def money_format(value):
    return f"NGN{Decimal(value):,.2f}"


def generate_otp():
    value = int(datetime.now().strftime("%H%M%S%f")) % 100000
    return f"{value:05d}"


def generate_account_number():
    digits = datetime.now().strftime("%H%M%S%f")[-10:]
    return digits
# "2" + digits


def make_reference(prefix):
    digits = datetime.now().strftime("%H%M%S%f")[-6:]
    return f"{prefix}-{digits}"


class BANKCONFIG:
    def __init__(self):
        self.conn = None
        self.mycursor = None
        self._ensure_database()
        self.conn = sql.connect(
            host=DB_HOST,
            user=DB_USER,
            database=BANK_DB,
            password=DB_PASSWORD,
        )
        self.conn.autocommit = False
        self.mycursor = self.conn.cursor(dictionary=True)
        self._pending_changes = {}
        self._ensure_schema()

    def _ensure_database(self):
        server_conn = sql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        try:
            server_conn.autocommit = True
            server_cursor = server_conn.cursor()
            server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{BANK_DB}`")
        finally:
            server_cursor.close()
            server_conn.close()

    def _ensure_schema(self):
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS customers (id INT AUTO_INCREMENT PRIMARY KEY, full_name VARCHAR(150) NOT NULL, email VARCHAR(190) NOT NULL UNIQUE, password_hash VARCHAR(64) NOT NULL, account_number VARCHAR(12) NOT NULL UNIQUE, balance DECIMAL(18,2) NOT NULL DEFAULT 0.00, pin_hash VARCHAR(64) NULL, phone_number VARCHAR(20) NULL, address VARCHAR(255) NULL, date_of_birth DATE NULL, gender VARCHAR(10) NULL, is_frozen BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INT AUTO_INCREMENT PRIMARY KEY, account_number VARCHAR(12) NOT NULL, transaction_type VARCHAR(30) NOT NULL, amount DECIMAL(18,2) NOT NULL, balance_after DECIMAL(18,2) NOT NULL, recipient_account_number VARCHAR(12) NULL, reference VARCHAR(128) NOT NULL, description VARCHAR(255) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (account_number) REFERENCES customers(account_number))")
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS email_otps (email VARCHAR(190) NOT NULL UNIQUE, otp_hash VARCHAR(64) NOT NULL, expires_at DATETIME NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        self._migrate_customers_schema()
        self.conn.commit()

    def _migrate_customers_schema(self):
        try:
            self.mycursor.execute("SELECT phone_number FROM customers LIMIT 1")
            self.mycursor.fetchone()
        except Exception:
            self.mycursor.execute("ALTER TABLE customers ADD COLUMN phone_number VARCHAR(20) NULL")
        try:
            self.mycursor.execute("SELECT address FROM customers LIMIT 1")
            self.mycursor.fetchone()
        except Exception:
            self.mycursor.execute("ALTER TABLE customers ADD COLUMN address VARCHAR(255) NULL")
        try:
            self.mycursor.execute("SELECT date_of_birth FROM customers LIMIT 1")
            self.mycursor.fetchone()
        except Exception:
            self.mycursor.execute("ALTER TABLE customers ADD COLUMN date_of_birth DATE NULL")
        try:
            self.mycursor.execute("SELECT gender FROM customers LIMIT 1")
            self.mycursor.fetchone()
        except Exception:
            self.mycursor.execute("ALTER TABLE customers ADD COLUMN gender VARCHAR(10) NULL")
        try:
            self.mycursor.execute("SELECT is_frozen FROM customers LIMIT 1")
            self.mycursor.fetchone()
        except Exception:
            self.mycursor.execute("ALTER TABLE customers ADD COLUMN is_frozen BOOLEAN NOT NULL DEFAULT FALSE")

    def _send_email(self, to_email, subject, body):
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = EMAIL_FROM
            msg["To"] = to_email

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context) as server:
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception:
            return False

    def send_email_otp(self, email):
        email = normalize_email(email)
        if not email_validate(email):
            return False

        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=2)

        try:
            self.mycursor.execute("DELETE FROM email_otps WHERE email=%s", (email,))
            self.mycursor.execute(
                "INSERT INTO email_otps(email, otp_hash, expires_at) VALUES(%s, %s, %s)",
                (email, otp_hash(otp), expires_at),
            )
            self.conn.commit()

            body = f"Your Shamskay Bank verification OTP is: {otp}\n\nThis code expires in 2 minutes."
            return self._send_email(email, "Shamskay Bank Email Verification OTP", body)
        except Exception:
            self.conn.rollback()
            return False

    def verify_email_otp(self, email, otp):
        email = normalize_email(email)
        try:
            self.mycursor.execute(
                "SELECT otp_hash, expires_at FROM email_otps WHERE email=%s",
                (email,),
            )
            record = self.mycursor.fetchone()
            if not record:
                return False

            if record["otp_hash"] != otp_hash(otp):
                return False

            if datetime.now() > record["expires_at"]:
                self.mycursor.execute("DELETE FROM email_otps WHERE email=%s", (email,))
                self.conn.commit()
                return False

            self.mycursor.execute("DELETE FROM email_otps WHERE email=%s", (email,))
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            return False

    def account_exists(self, account_number):
        try:
            self.mycursor.execute("SELECT id FROM customers WHERE account_number=%s", (account_number,))
            return self.mycursor.fetchone() is not None
        except Exception:
            return False

    def _generate_unique_account_number(self):
        for _ in range(100):
            account_number = generate_account_number()
            if not self.account_exists(account_number):
                return account_number
        raise RuntimeError("Could not generate a unique account number.")

    def create_customer(self, full_name, email, password, confirm_password, phone_number="", address="", date_of_birth=None, gender=None, otp_verified=False):
        if not otp_verified:
            return {"status": False, "message": "Email OTP verification is required before account can be created."}

        email = normalize_email(email)
        full_name = " ".join(full_name.strip().split())
        phone_number = phone_number.strip()
        address = address.strip()

        if not full_name:
            return {"status": False, "message": "Full name is a requirement."}

        if not email_validate(email):
            return {"status": False, "message": "Invalid email format. Use the form name@gmail.com"}

        if not validate_password(password):
            return {"status": False, "message": "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."}

        if password != confirm_password:
            return {"status": False, "message": "Password and confirmed password do not match."}

        existing = self.get_customer_by_email(email)
        if existing:
            return {"status": False, "message": "This email is already registered. Please use another email."}

        if phone_number:
            existing_phone = self.get_customer_by_phone(phone_number)
            if existing_phone:
                return {"status": False, "message": "This phone number is already registered. Please use another phone number."}

        account_number = self._generate_unique_account_number()

        try:
            normalized_dob = date_of_birth.strip() if isinstance(date_of_birth, str) else None
            self.mycursor.execute(
                """
                INSERT INTO customers(full_name, email, password_hash, account_number, balance, phone_number, address, date_of_birth, gender)
                VALUES(%s, %s, %s, %s, 0.00, %s, %s, %s, %s)
                """,
                (full_name, email, password_hash(password), account_number, phone_number or None, address or None, normalized_dob or None, gender or None),
            )
            self.conn.commit()
            return {
                "status": True,
                "message": "Registration successful.",
                "data": self.get_customer_by_account(account_number),
            }
        except sql.errors.IntegrityError:
            self.conn.rollback()
            return {"status": False, "message": "Email or account number already exists."}
        except Exception as err:
            self.conn.rollback()
            return {"status": False, "message": str(err)}

    def update_address(self, account_number, new_address):
        account_number = (account_number or "").strip()
        new_address = (new_address or "").strip()

        if not new_address:
            return {"status": False, "message": "Address cannot be empty."}

        try:
            self.mycursor.execute(
                "SELECT address FROM customers WHERE account_number=%s",
                (account_number,),
            )
            customer = self.mycursor.fetchone()
            if not customer:
                return {"status": False, "message": "Account not found."}

            old_address = customer.get("address") or ""
            if old_address == new_address:
                return {"status": True, "message": "Address is already up to date."}

            self.mycursor.execute(
                "UPDATE customers SET address=%s WHERE account_number=%s",
                (new_address, account_number),
            )
            self.conn.commit()
            return {"status": True, "message": "Address updated successfully."}
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def login_customer(self, email, password):
        email = normalize_email(email)
        try:
            self.mycursor.execute(
                """
                SELECT id, full_name, email, account_number, balance, password_hash, phone_number, address, date_of_birth, gender, created_at
                FROM customers
                WHERE email=%s
                """,
                (email,),
            )
            customer = self.mycursor.fetchone()

            if not customer:
                return {"status": False, "message": "Email does not exist."}

            if customer.get("is_frozen"):
                return {"status": False, "message": "Your account has been frozen. Contact admin."}

            if not password_check(password, customer["password_hash"]):
                return {"status": False, "message": "Incorrect password."}

            return {
                "status": True,
                "message": f"Welcome back, {customer['full_name']}.",
                "data": {
                    "id": customer["id"],
                    "full_name": customer["full_name"],
                    "email": customer["email"],
                    "account_number": customer["account_number"],
                    "balance": customer["balance"],
                    "phone_number": customer.get("phone_number"),
                    "address": customer.get("address"),
                    "date_of_birth": customer.get("date_of_birth"),
                    "gender": customer.get("gender"),
                    "is_frozen": customer.get("is_frozen"),
                    "created_at": customer["created_at"],
                },
            }
        except Exception as e:
            return {"status": False, "message": str(e)}

    def get_customer_by_account(self, account_number):
        try:
            self.mycursor.execute(
                """
                SELECT id, full_name, email, account_number, balance, phone_number, address, date_of_birth, gender, is_frozen, created_at
                FROM customers
                WHERE account_number=%s
                """,
                (account_number,),
            )
            return self.mycursor.fetchone()
        except Exception:
            return None

    def get_customer_by_email(self, email):
        email = normalize_email(email)
        try:
            self.mycursor.execute(
                "SELECT id, account_number, password_hash FROM customers WHERE email=%s LIMIT 1",
                (email,),
            )
            return self.mycursor.fetchone()
        except Exception:
            return None

    def get_customer_by_phone(self, phone_number):
        try:
            self.mycursor.execute(
                "SELECT id FROM customers WHERE phone_number=%s LIMIT 1",
                (phone_number,),
            )
            return self.mycursor.fetchone()
        except Exception:
            return None

    def get_password_hash_by_account(self, account_number):
        try:
            self.mycursor.execute(
                "SELECT password_hash FROM customers WHERE account_number=%s",
                (account_number,),
            )
            return self.mycursor.fetchone()
        except Exception:
            return None

    def get_pin_hash_by_account(self, account_number):
        try:
            self.mycursor.execute("SELECT pin_hash FROM customers WHERE account_number=%s", (account_number,))
            return self.mycursor.fetchone()
        except Exception:
            return None

    def get_email_by_account(self, account_number):
        try:
            self.mycursor.execute("SELECT email FROM customers WHERE account_number=%s", (account_number,))
            row = self.mycursor.fetchone()
            return row["email"] if row else None
        except Exception:
            return None

    def _request_otp_verification(self, account_number, context_label, apply_callback, success_message, expiry_minutes=2):
        email = self.get_email_by_account(account_number)
        if not email:
            return {"status": False, "message": "Customer email not found."}
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
        self._pending_changes[account_number] = {
            "otp": otp,
            "context": context_label,
            "apply_callback": apply_callback,
            "success_message": success_message,
            "expires_at": expires_at,
        }
        body = f"Your Shamskay Bank verification OTP for {context_label} is: {otp}\n\nThis code expires in {expiry_minutes} minutes."
        sent = self._send_email(email, f"Shamskay Bank {context_label} OTP", body)
        if not sent:
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": "Failed to send verification OTP. Please try again."}
        return {"status": True, "message": "Verification OTP sent to your email."}

    def _verify_and_apply(self, account_number, otp):
        pending = self._pending_changes.get(account_number)
        if not pending:
            return {"status": False, "message": "Please request verification OTP first."}
        expires_at = pending.get("expires_at")
        if expires_at and datetime.now() > expires_at:
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": "Verification OTP has expired. Please request a new one."}
        if pending["otp"] != otp:
            return {"status": False, "message": "Invalid verification OTP."}
        try:
            pending["apply_callback"]()
            self.conn.commit()
            self._pending_changes.pop(account_number, None)
            return {"status": True, "message": pending["success_message"]}
        except Exception as error:
            self.conn.rollback()
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": str(error)}

    def get_customer_for_update(self, account_number):
        try:
            self.mycursor.execute(
                """
                SELECT account_number, full_name, balance
                FROM customers
                WHERE account_number=%s
                FOR UPDATE
                """,
                (account_number,),
            )
            return self.mycursor.fetchone()
        except Exception:
            return None

    def create_transaction_pin(self, account_number, pin, verify_pin):
        if not validate_pin(pin):
            return {"status": False, "message": "PIN must be exactly 4 digits."}

        if pin != verify_pin:
            return {"status": False, "message": "PIN and verified PIN do not match."}

        customer = self.get_pin_hash_by_account(account_number)
        if not customer:
            return {"status": False, "message": "Customer not found."}

        if customer["pin_hash"]:
            return {"status": False, "message": "Transaction PIN already exists. Change it instead."}

        try:
            self.mycursor.execute(
                "UPDATE customers SET pin_hash=%s WHERE account_number=%s",
                (pin_hash(pin), account_number),
            )
            self.conn.commit()
            return {"status": True, "message": "Your 4-digit transaction PIN has been created successfully"}

        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def change_transaction_pin(self, account_number, old_pin, new_pin, verify_pin):
        if not validate_pin(old_pin) or not validate_pin(new_pin):
            return {"status": False, "message": "PIN must be exactly 4 digits."}

        if new_pin != verify_pin:
            return {"status": False, "message": "New PIN and verified PIN do not match."}

        customer = self.get_pin_hash_by_account(account_number)
        if not customer:
            return {"status": False, "message": "Customer not found."}

        if not customer["pin_hash"]:
            return {"status": False, "message": "Create a transaction PIN first."}

        if not pin_check(old_pin, customer["pin_hash"]):
            return {"status": False, "message": "Old PIN is incorrect."}

        return self._request_otp_verification(
            account_number,
            "Change Transaction PIN",
            lambda: self.mycursor.execute(
                "UPDATE customers SET pin_hash=%s WHERE account_number=%s",
                (pin_hash(new_pin), account_number),
            ),
            "Transaction PIN changed successfully.",
        )

    def check_transaction_pin(self, account_number, pin):
        customer = self.get_pin_hash_by_account(account_number)
        if not customer:
            return {"status": False, "message": "Customer not found."}

        if not customer["pin_hash"]:
            return {"status": False, "message": "Create a transaction PIN before using this feature."}

        if not pin_check(pin, customer["pin_hash"]):
            return {"status": False, "message": "Incorrect transaction PIN."}

        return {"status": True, "message": "PIN verified."}

    def change_password(self, account_number, old_password, new_password, confirm_password):
        customer = self.get_password_hash_by_account(account_number)
        if not customer:
            return {"status": False, "message": "Customer not found."}

        if not password_check(old_password, customer["password_hash"]):
            return {"status": False, "message": "Current password is incorrect."}

        if password_check(new_password, customer["password_hash"]):
            return {"status": False, "message": "New password cannot be the same as the current password."}

        if new_password != confirm_password:
            return {"status": False, "message": "New password and verified password do not match."}

        if not validate_password(new_password):
            return {"status": False, "message": "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."}

        return self._request_otp_verification(
            account_number,
            "Password Change",
            lambda: self.mycursor.execute(
                "UPDATE customers SET password_hash=%s WHERE account_number=%s",
                (password_hash(new_password), account_number),
            ),
            "Password changed successfully.",
        )

    def send_forgot_password_otp(self, email):
        email = normalize_email(email)
        if not email_validate(email):
            return {"status": False, "message": "Invalid email format. Use the form name@gmail.com"}

        customer = self.get_customer_by_email(email)
        if not customer:
            return {"status": False, "message": "Email does not exist."}

        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=2)
        account_number = customer["account_number"]
        self._pending_changes[account_number] = {
            "otp": otp,
            "context": "Password Reset",
            "expires_at": expires_at,
        }

        body = f"Your Shamskay Bank password reset OTP is: {otp}\n\nThis code expires in 2 minutes."
        sent = self._send_email(email, "Shamskay Bank Password Reset OTP", body)
        if not sent:
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": "Failed to send password reset OTP. Please try again."}
        return {"status": True, "message": "Password reset OTP sent to your email."}

    def reset_forgot_password(self, email, new_password, confirm_password, otp):
        email = normalize_email(email)
        if not email_validate(email):
            return {"status": False, "message": "Invalid email format. Use the form name@gmail.com"}

        customer = self.get_customer_by_email(email)
        if not customer:
            return {"status": False, "message": "Email does not exist."}

        if not validate_password(new_password):
            return {"status": False, "message": "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."}

        if new_password != confirm_password:
            return {"status": False, "message": "New password and verified password do not match."}

        if password_check(new_password, customer["password_hash"]):
            return {"status": False, "message": "New password cannot be the same as the current password."}

        account_number = customer["account_number"]
        pending = self._pending_changes.get(account_number)
        if not pending or pending.get("context") != "Password Reset":
            return {"status": False, "message": "Please request a password reset OTP first."}

        expires_at = pending.get("expires_at")
        if expires_at and datetime.now() > expires_at:
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": "Password reset OTP has expired. Please request a new one."}

        if pending["otp"] != otp:
            return {"status": False, "message": "Invalid password reset OTP."}

        try:
            self.mycursor.execute(
                "UPDATE customers SET password_hash=%s WHERE account_number=%s",
                (password_hash(new_password), account_number),
            )
            self.conn.commit()
            self._pending_changes.pop(account_number, None)
            return {"status": True, "message": "Password reset successful. You can now login with your new password."}
        except Exception as error:
            self.conn.rollback()
            self._pending_changes.pop(account_number, None)
            return {"status": False, "message": str(error)}

    def _record_transaction(
        self,
        account_number,
        transaction_type,
        amount,
        balance_after,
        recipient_account_number,
        reference,
        description,
    ):
        self.mycursor.execute(
            """
            INSERT INTO transactions(
                account_number,
                transaction_type,
                amount,
                balance_after,
                recipient_account_number,
                reference,
                description
            )
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                account_number,
                transaction_type,
                amount,
                balance_after,
                recipient_account_number,
                reference,
                description,
            ),
        )

    def _credit_account(self, account_number, amount, transaction_type, recipient_account_number, reference, description):
        self.mycursor.execute(
            "SELECT balance FROM customers WHERE account_number=%s FOR UPDATE",
            (account_number,),
        )
        row = self.mycursor.fetchone()
        if not row:
            return {"status": False, "message": "Account not found."}

        new_balance = Decimal(row["balance"]) + amount
        self.mycursor.execute(
            "UPDATE customers SET balance=%s WHERE account_number=%s",
            (new_balance, account_number),
        )
        self._record_transaction(
            account_number,
            transaction_type,
            amount,
            new_balance,
            recipient_account_number,
            reference,
            description,
        )
        return {"status": True, "new_balance": new_balance}

    def _debit_account(self, account_number, amount, transaction_type, recipient_account_number, reference, description):
        self.mycursor.execute(
            "SELECT balance FROM customers WHERE account_number=%s FOR UPDATE",
            (account_number,),
        )
        row = self.mycursor.fetchone()
        if not row:
            return {"status": False, "message": "Account not found."}

        current_balance = Decimal(row["balance"])
        if current_balance < amount:
            return {"status": False, "message": "Insufficient balance."}

        new_balance = current_balance - amount
        self.mycursor.execute(
            "UPDATE customers SET balance=%s WHERE account_number=%s",
            (new_balance, account_number),
        )
        self._record_transaction(
            account_number,
            transaction_type,
            amount,
            new_balance,
            recipient_account_number,
            reference,
            description,
        )
        return {"status": True, "new_balance": new_balance}

    def deposit_money(self, account_number, amount):
        amount = validate_amount(amount)
        if amount is None:
            return {"status": False, "message": "Enter a valid deposit amount."}

        try:
            reference = make_reference("DEP")
            result = self._credit_account(account_number, amount, "deposit", None, reference, "Cash deposit")
            if not result["status"]:
                return result

            self.conn.commit()
            return {
                "status": True,
                "message": f"Deposit successful. New balance: {money_format(result['new_balance'])}",
            }
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def buy_airtime(self, account_number, pin, phone_number, amount, provider):
        pin_result = self.check_transaction_pin(account_number, pin)
        if not pin_result["status"]:
            return pin_result

        amount = validate_amount(amount)
        if amount is None:
            return {"status": False, "message": "Enter a valid airtime amount."}
        if amount < Decimal("0.50"):
            return {"status": False, "message": "Minimum airtime purchase is NGN50.00."}

        phone_number = phone_number.strip()
        if not re.fullmatch(r"\d{11}", phone_number):
            return {"status": False, "message": "Airtime phone number must be exactly 11 digits."}
        provider = provider.strip() or "Unknown"

        try:
            reference = make_reference("AIR")
            result = self._debit_account(
                account_number,
                amount,
                "airtime_purchase",
                None,
                reference,
                f"Airtime purchase for {phone_number} via {provider}",
            )
            if not result["status"]:
                return result

            self.conn.commit()
            return {
                "status": True,
                "message": f"Airtime purchase successful. New balance: {money_format(result['new_balance'])}",
            }
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def transfer_money(self, sender_account, recipient_account, pin, amount):
        pin_result = self.check_transaction_pin(sender_account, pin)
        if not pin_result["status"]:
            return pin_result

        amount = validate_amount(amount)
        if amount is None:
            return {"status": False, "message": "Enter a valid transfer amount."}
        if amount < Decimal("1.00"):
            return {"status": False, "message": "Minimum transfer amount is NGN100.00."}

        sender_account = sender_account.strip()
        recipient_account = recipient_account.strip()

        if sender_account == recipient_account:
            return {"status": False, "message": "You cannot transfer to your own account."}

        try:
            sender = self.get_customer_for_update(sender_account)
            if not sender:
                return {"status": False, "message": "Sender account not found."}

            recipient = self.get_customer_for_update(recipient_account)
            if not recipient:
                return {"status": False, "message": "Recipient account not found."}

            reference = make_reference("TRF")
            debit_result = self._debit_account(
                sender_account,
                amount,
                "transfer_out",
                recipient_account,
                reference,
                f"Transfer to {recipient['full_name']}",
            )
            if not debit_result["status"]:
                return debit_result

            credit_result = self._credit_account(
                recipient_account,
                amount,
                "transfer_in",
                sender_account,
                reference,
                f"Transfer from {sender['full_name']}",
            )
            if not credit_result["status"]:
                return credit_result

            self.conn.commit()
            return {
                "status": True,
                "message": f"Transfer successful. New balance: {money_format(debit_result['new_balance'])}",
                "data": {
                    "reference": reference,
                    "recipient": recipient["full_name"],
                    "recipient_account": recipient_account,
                },
            }
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def pay_bill(self, account_number, pin, biller, customer_id, amount):
        pin_result = self.check_transaction_pin(account_number, pin)
        if not pin_result["status"]:
            return pin_result

        amount = validate_amount(amount)
        if amount is None:
            return {"status": False, "message": "Enter a valid bill amount."}
        if amount < Decimal("1.00"):
            return {"status": False, "message": "Minimum bill payment is NGN100.00."}

        biller = biller.strip() or "Unknown"
        customer_id = customer_id.strip()
        if not re.fullmatch(r"\d{11}", customer_id):
            return {"status": False, "message": "Biller smart card number must be exactly 11 digits."}

        try:
            reference = make_reference("BILL")
            result = self._debit_account(
                account_number,
                amount,
                "bill_payment",
                None,
                reference,
                f"Bill payment to {biller} for {customer_id}",
            )
            if not result["status"]:
                return result

            self.conn.commit()
            return {
                "status": True,
                "message": f"Bill payment successful. New balance: {money_format(result['new_balance'])}",
            }
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def view_balance(self, account_number):
        customer = self.get_customer_by_account(account_number)
        if not customer:
            return {"status": False, "message": "Account not found."}
        return {"status": True, "data": customer}

    def view_transactions(self, account_number, limit=None):
        if limit is not None:
            try:
                limit = int(limit)
            except Exception:
                limit = None

        try:
            if limit is not None:
                self.mycursor.execute(
                    """
                    SELECT id, transaction_type, amount, balance_after, recipient_account_number, reference, description, created_at
                    FROM transactions
                    WHERE account_number=%s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (account_number, limit),
                )
            else:
                self.mycursor.execute(
                    """
                    SELECT id, transaction_type, amount, balance_after, recipient_account_number, reference, description, created_at
                    FROM transactions
                    WHERE account_number=%s
                    ORDER BY created_at DESC, id DESC
                    """,
                    (account_number,),
                )
            transactions = self.mycursor.fetchall()
            if not transactions:
                return {"status": False, "message": "No transactions found."}
            return {"status": True, "data": transactions}
        except Exception as error:
            return {"status": False, "message": str(error)}

def admin_login(self):
        admin_password = ("SHAMSKAY").strip().upper()
        password = input("Admin Password: ").strip()
        if password != admin_password:
            return {"status": False, "message": "Invalid admin password."}
        return {"status": True, "message": "Admin login successful."}

    def get_all_customers(self):
        try:
            self.mycursor.execute(
                """
                SELECT id, full_name, email, account_number, balance, phone_number, address, date_of_birth, gender, is_frozen, created_at
                FROM customers
                ORDER BY created_at DESC
                """
            )
            customers = self.mycursor.fetchall()
            if not customers:
                return {"status": False, "message": "No customers found."}
            return {"status": True, "data": customers}
        except Exception as error:
            return {"status": False, "message": str(error)}

    def _freeze_account(self, account_number):
        try:
            self.mycursor.execute(
                "UPDATE customers SET is_frozen=TRUE WHERE account_number=%s",
                (account_number,),
            )
            self.conn.commit()
            if self.mycursor.rowcount > 0:
                return {"status": True, "message": "Account frozen successfully."}
            return {"status": False, "message": "Account not found."}
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def _unfreeze_account(self, account_number):
        try:
            self.mycursor.execute(
                "UPDATE customers SET is_frozen=FALSE WHERE account_number=%s",
                (account_number,),
            )
            self.conn.commit()
            if self.mycursor.rowcount > 0:
                return {"status": True, "message": "Account unfrozen successfully."}
            return {"status": False, "message": "Account not found."}
        except Exception as error:
            self.conn.rollback()
            return {"status": False, "message": str(error)}

    def is_account_frozen(self, account_number):
        try:
            self.mycursor.execute(
                "SELECT is_frozen FROM customers WHERE account_number=%s",
                (account_number,),
            )
            row = self.mycursor.fetchone()
            return row["is_frozen"] if row else False
        except Exception:
            return False
