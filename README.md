**SHAMSKAY-BANK**

This is a learning-wise bank app project which allow user (customer) to perform various transactions which are secured.

**SHAMSKAY BANK APP**

SHAMSKAY BANK APP is a console-based banking application built with Python and MySQL. It provides a user-facing banking interface for registration, login, deposits, transfers, airtime purchase, bill payment, transaction history, PIN management, password changes, profile viewing, and address editing.

**REPOSITORY CONTENTS**

**`BANKAPP.py`**

`BANKAPP.py` is the main user interface file which is committed to this repository and it contains the console menus and user workflow for the banking system.

The following are the features in `BANKAPP.py`:

- Home menu
- Customer registration
- Customer login
- Dashboard menu
- View balance
- Deposit money
- Transfer money
- Buy airtime
- Pay bills
- View transaction history
- Create/change transaction PIN
- Change password
- View profile
- Edit address

**`BANKCONFIG.py`**

The `BANKCONFIG.py` is the private backend file and is intentionally not committed to this repository but a template was made available.

'BANKCONFIG.py' contains the following backend logic:

- MySQL database connection
- Database/table setup
- Customer creation and login
- Password hashing
- PIN hashing
- OTP generation and verification
- Email OTP sending
- Deposit, transfer, airtime, and bill payment processing
- Transaction history retrieval
- Money formatting and validation helpers

**`BANKCONFIG_TEMPLATE.py`**

`BANKCONFIG_TEMPLATE.py` is a placeholder file showing that the private backend is not included in the public repository.

**`schema.sql`**

`schema.sql` contains the database schema used by the application. It defines the main database tables created i.e customers, transactions, and email OTP records.

**Features**

- User registration with email OTP verification
- 4-digit email verification OTP
- Login authentication
- Account balance viewing
- Cash deposit
- Money transfer
- Airtime purchase
- Bill payment
- Transaction PIN creation and change
- Password change with OTP verification
- Profile viewing
- Address update
- Transaction history display

**Requirements**

- Python 3.x
- MySQL Server
- `mysql-connector-python`
- `pyttsx3` for voice output

Install dependencies:

```bash
pip install mysql-connector-python
pip install pyttsx3
```

**Setup**

1. Started MySQL server.
2. `BANKCONFIG.py` was kept in the same folder as `BANKAPP.py`.
3. Email credentials were updated in the private database in `BANKCONFIG.py`.
4. The application 'BANKAPP.py' was run:


**OTP Settings**

- Registration email verification OTP expires after 2 minutes.
- Password/PIN change OTP expires after 2 minutes.
- Email verification OTP is generated as a 4-digit code.

Only public files such as `BANKAPP.py`, `README.md`, and optional template/setup files should be pushed to a public repository.

**Security Notes**

This project hashes passwords, PINs, and OTPs before storing them in the database.
