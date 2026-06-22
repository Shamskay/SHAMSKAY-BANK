# SHAMSKAY-BANK

This is a learning-wise bank app project which allows users/customers to perform various secured banking transactions.

## SHAMSKAY BANK APP

SHAMSKAY BANK APP is a console-based banking application built with Python and MySQL. It provides a user-facing banking interface for registration, login, deposits, transfers, airtime purchase, bill payment, transaction history, PIN management, password changes, forgot password, profile viewing, and address editing.

## Repository Contents

### `BANKAPP.py`

`BANKAPP.py` is the main user interface file committed to this repository. It contains the console menus and user workflow for the banking system.

The following are the features in `BANKAPP.py`:

- Home menu
- Customer registration
- Customer login
- Forgot password with email OTP verification
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

### `BANKCONFIG.py`

`BANKCONFIG.py` is the private backend file and is intentionally not committed to this repository, but a template is available.

`BANKCONFIG.py` contains backend logic such as:

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

### `BANKCONFIG_TEMPLATE.py`

`BANKCONFIG_TEMPLATE.py` is a placeholder file showing that the private backend is not included in the public repository.

### `schema.sql`

`schema.sql` contains the database schema used by the application. It defines the main database tables created, including customers, transactions, and email OTP records.

## Features

- User registration with email OTP verification
- Forgot password with email OTP verification
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

## Requirements

- Python 3.x
- MySQL Server
- `mysql-connector-python`

Install dependencies:

```bash
pip install mysql-connector-python
pip install pyttsx3
```
## Modules

The following modules were used:
- pyttsx3
- hashlib
- re
- smtplib
- ssl
- datetime
- decimal
- email.mime.text

## Setup

1. The MySQL server was started.
2. `BANKCONFIG.py` (private) was kept in the same folder as `BANKAPP.py`.
3. Private database and email credentials updated in the `BANKCONFIG.py`.
4. The application, `BANKAPP.py`, was run:


## OTP Settings

- Registration email verification OTP expires after 2 minutes.
- Password/PIN/forgot password OTP expires after 2 minutes.
- Email verification OTP is generated as a 4-digit code.

## Git Privacy Setup

Only public files such as `BANKAPP.py`, `README.md`, and optional template/setup files were pushed to a public repository.

The real backend file is ignored with `.gitignore`:


## Security Notes

This project hashes passwords, PINs, and OTPs before storing them in the database.
