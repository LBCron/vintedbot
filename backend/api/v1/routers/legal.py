"""
Legal endpoints - Terms of Service, Privacy Policy, Disclaimers
"""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/legal", tags=["legal"])


class LegalDocument(BaseModel):
    """Legal document response"""
    title: str
    content: str
    last_updated: str
    version: str


@router.get("/terms", response_model=LegalDocument)
async def get_terms_of_service():
    """
    Get Terms of Service

    Returns:
        Terms of Service document
    """
    return LegalDocument(
        title="Terms of Service",
        version="1.0",
        last_updated="2024-01-01",
        content="""
# Terms of Service - VintedBot

**Last Updated: January 1, 2024**

## 1. Acceptance of Terms

By accessing and using VintedBot ("the Service"), you accept and agree to be bound by the terms and provision of this agreement.

## 2. Use at Your Own Risk

[WARN] **IMPORTANT DISCLAIMER:**

VintedBot automates interactions with Vinted.com, which may violate Vinted's Terms of Service. By using this service, you acknowledge and accept the following risks:

- **Account Suspension/Ban**: Vinted may suspend or permanently ban your account for using automation tools
- **No Guarantees**: We provide no guarantees that automation will work or that your account will remain active
- **Third-Party Service**: Vinted is not affiliated with VintedBot and may take action against automation users
- **Legal Responsibility**: You are solely responsible for any consequences resulting from using this service

## 3. Prohibited Activities

You agree NOT to:

- Use the service for any illegal purposes
- Attempt to bypass Vinted's security measures
- Spam, harass, or abuse other Vinted users
- Use the service in a way that damages Vinted's or VintedBot's infrastructure
- Share your account credentials with others
- Reverse engineer or attempt to extract our source code

## 4. Data and Privacy

- We store your Vinted session cookies encrypted
- We do not share your data with third parties
- We may use anonymized usage data for analytics
- You can request data deletion at any time

## 5. Service Availability

- The service is provided "as is" without warranties
- We may suspend, modify, or discontinue the service at any time
- We are not liable for service interruptions or data loss

## 6. Payments and Refunds

- Subscription fees are non-refundable
- You can cancel your subscription at any time
- Cancellation takes effect at the end of your billing period
- We reserve the right to change pricing with 30 days notice

## 7. Intellectual Property

- All content, features, and functionality are owned by VintedBot
- You may not copy, modify, or distribute our software
- Your content remains your property

## 8. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:

- We are not liable for any damages arising from service use
- We are not responsible for Vinted account bans or suspensions
- Our total liability is limited to the amount you paid in the last 12 months
- We are not liable for indirect, incidental, or consequential damages

## 9. Indemnification

You agree to indemnify and hold harmless VintedBot from any claims, damages, or expenses arising from:

- Your use of the service
- Your violation of these terms
- Your violation of Vinted's terms of service
- Your violation of any third-party rights

## 10. Changes to Terms

We reserve the right to modify these terms at any time. Continued use of the service after changes constitutes acceptance of new terms.

## 11. Termination

We may terminate your access to the service at any time, with or without cause, with or without notice.

## 12. Governing Law

These terms are governed by the laws of [Your Jurisdiction], without regard to conflict of law provisions.

## 13. Contact

For questions about these terms, contact: support@vintedbot.com

---

**BY USING THIS SERVICE, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE TO BE BOUND BY THESE TERMS.**
        """.strip()
    )


@router.get("/privacy", response_model=LegalDocument)
async def get_privacy_policy():
    """
    Get Privacy Policy

    Returns:
        Privacy Policy document
    """
    return LegalDocument(
        title="Privacy Policy",
        version="1.0",
        last_updated="2024-01-01",
        content="""
# Privacy Policy - VintedBot

**Last Updated: January 1, 2024**

## 1. Information We Collect

### Account Information
- Email address
- Encrypted password (hashed with Argon2)
- Subscription plan and payment information

### Vinted Session Data
- Vinted session cookies (encrypted with AES-256)
- Vinted account information
- Listing data, photos, and descriptions

### Usage Data
- API request logs
- Error logs and debugging information
- Feature usage analytics
- Device information and IP addresses

### Payment Information
- Processed through Stripe (we do not store credit card details)
- Billing history and invoices

## 2. How We Use Your Information

We use collected information to:

- Provide and maintain the service
- Process automation tasks on Vinted
- Improve our service and develop new features
- Communicate with you about your account
- Process payments and prevent fraud
- Comply with legal obligations
- Analyze usage patterns and optimize performance

## 3. Data Security

We implement industry-standard security measures:

- **Encryption**: Vinted session cookies encrypted with AES-256
- **Password Hashing**: Argon2 (memory-hard algorithm)
- **HTTPS**: All communication encrypted with TLS
- **Secure Storage**: SQLite database with restricted access
- **Regular Backups**: Automated encrypted backups

However, no method of transmission over the Internet is 100% secure. We cannot guarantee absolute security.

## 4. Data Retention

- **Account Data**: Retained while your account is active
- **Logs**: Retained for 90 days
- **Backups**: Retained for 30 days
- **Deleted Accounts**: Data purged within 30 days of account deletion

## 5. Data Sharing

We do NOT sell or rent your personal information.

We may share data with:

- **Service Providers**: Stripe (payments), hosting providers
- **Legal Requirements**: When required by law or to protect our rights
- **Business Transfer**: In case of merger, acquisition, or sale

## 6. Your Rights

You have the right to:

- **Access**: Request a copy of your data
- **Correction**: Update inaccurate information
- **Deletion**: Request account and data deletion
- **Export**: Download your data in JSON format
- **Opt-Out**: Unsubscribe from marketing emails
- **Restriction**: Limit how we process your data

To exercise these rights, contact: privacy@vintedbot.com

## 7. Cookies

We use cookies for:

- Authentication (httpOnly, secure cookies)
- Session management
- Analytics and performance monitoring

You can disable cookies in your browser, but this may affect functionality.

## 8. Third-Party Services

We integrate with:

- **Vinted**: We access Vinted on your behalf (subject to their privacy policy)
- **Stripe**: Payment processing (subject to Stripe's privacy policy)
- **OpenAI**: AI photo analysis (images sent to OpenAI API)

## 9. International Data Transfers

Your data may be transferred to and stored in countries outside your residence. We ensure appropriate safeguards are in place.

## 10. Children's Privacy

Our service is not intended for users under 18. We do not knowingly collect data from children.

## 11. Changes to Privacy Policy

We may update this policy from time to time. We will notify you of significant changes via email or service notification.

## 12. Contact Us

For privacy-related questions or requests:

- Email: privacy@vintedbot.com
- Response time: Within 30 days

---

**Last Updated**: January 1, 2024
        """.strip()
    )


@router.get("/disclaimer", response_model=LegalDocument)
async def get_disclaimer():
    """
    Get Service Disclaimer

    Returns:
        Disclaimer document
    """
    return LegalDocument(
        title="Service Disclaimer",
        version="1.0",
        last_updated="2024-01-01",
        content="""
# Service Disclaimer - VintedBot

**[WARN] READ CAREFULLY BEFORE USING THIS SERVICE [WARN]**

## 1. No Affiliation with Vinted

VintedBot is **NOT affiliated with, endorsed by, or sponsored by Vinted**. This is an independent third-party service.

## 2. Terms of Service Violation

Using automation tools may **VIOLATE Vinted's Terms of Service**. Vinted explicitly prohibits:

- Automated access to their platform
- Scraping or data extraction
- Automated account actions
- Circumventing security measures

## 3. Account Ban Risk

**[WARN] HIGH RISK OF ACCOUNT BAN [WARN]**

Using VintedBot may result in:

- Temporary account suspension
- Permanent account ban
- Loss of listings and sales history
- Loss of funds in your Vinted wallet

**WE CANNOT PREVENT BANS OR RECOVER BANNED ACCOUNTS**

## 4. No Guarantees

We provide **NO GUARANTEES** that:

- The service will work as expected
- Your Vinted account will remain active
- Automation will not be detected
- Features will continue to work if Vinted changes their platform
- You will see increased sales or visibility

## 5. Detection Methods

Vinted employs various anti-automation measures:

- CAPTCHA challenges
- Rate limiting
- Behavioral analysis
- Device fingerprinting
- IP tracking

**We attempt to minimize detection but cannot guarantee success.**

## 6. Legal Consequences

Depending on your jurisdiction and Vinted's actions, automation may result in:

- Civil liability
- Account termination
- Loss of access to funds
- Legal action by Vinted

## 7. User Responsibility

By using this service, you acknowledge that:

- You are solely responsible for any consequences
- You accept the risk of account suspension/ban
- You will not hold VintedBot liable for any damages
- You understand that Vinted may take action against you
- You agree to use the service ethically and responsibly

## 8. Service Limitations

VintedBot:

- Cannot bypass CAPTCHAs (we abort when detected)
- Cannot guarantee listing visibility
- Cannot prevent rate limiting by Vinted
- May stop working if Vinted changes their platform
- Requires valid Vinted session cookies

## 9. Ethical Use Only

You agree to use VintedBot for:

- [OK] Managing your own legitimate listings
- [OK] Saving time on repetitive tasks
- [OK] Analyzing your own performance

You agree NOT to use VintedBot for:

- [ERROR] Spamming users
- [ERROR] Creating fake accounts
- [ERROR] Manipulating prices unfairly
- [ERROR] Harassing other users
- [ERROR] Any illegal activities

## 10. Alternative Recommendations

Consider these lower-risk alternatives:

- Use Vinted's official features
- Manually perform actions
- Follow Vinted's guidelines
- Consider Vinted's paid promotion features

## 11. No Warranty

THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

## 12. Assumption of Risk

**BY USING THIS SERVICE, YOU EXPLICITLY ASSUME ALL RISKS** associated with automation on Vinted.

---

## Final Warning

**THINK CAREFULLY BEFORE PROCEEDING**

If you are not comfortable with the risks outlined above, **DO NOT USE THIS SERVICE**.

We recommend:
1. Reading Vinted's Terms of Service
2. Understanding the consequences
3. Starting with low-frequency automation
4. Monitoring your account for warnings
5. Being prepared for potential account loss

**YOU HAVE BEEN WARNED.**

---

**Last Updated**: January 1, 2024
        """.strip()
    )


@router.get("/acceptable-use", response_model=LegalDocument)
async def get_acceptable_use_policy():
    """
    Get Acceptable Use Policy

    Returns:
        Acceptable Use Policy document
    """
    return LegalDocument(
        title="Acceptable Use Policy",
        version="1.0",
        last_updated="2024-01-01",
        content="""
# Acceptable Use Policy - VintedBot

## Permitted Uses

You may use VintedBot to:

- [OK] Automate management of your own legitimate Vinted listings
- [OK] Analyze your own listing performance
- [OK] Save time on repetitive tasks
- [OK] Generate listing descriptions from photos
- [OK] Bump your listings within reasonable frequency

## Prohibited Uses

You may NOT use VintedBot to:

- [ERROR] Create or manage fake/fraudulent accounts
- [ERROR] Spam users with unsolicited messages
- [ERROR] Scrape data from other users without permission
- [ERROR] Manipulate prices to unfair levels
- [ERROR] Circumvent Vinted's security measures
- [ERROR] Harass, abuse, or threaten other users
- [ERROR] Sell prohibited items
- [ERROR] Engage in money laundering or fraud
- [ERROR] Violate any laws or regulations
- [ERROR] Overload our servers with excessive requests

## Enforcement

Violations of this policy may result in:

- Warning notification
- Service suspension
- Account termination
- Legal action if necessary

## Reporting Violations

To report a violation: abuse@vintedbot.com

---

**Last Updated**: January 1, 2024
        """.strip()
    )
