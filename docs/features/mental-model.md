# Mental Model Integration

First-of-its-kind integration with Mental CLI for domain-aware skills.

## What is Mental Model?

[Mental](https://github.com/mental-model/mental) externalizes codebase understanding:

- **Domains**: Order, Payment, User
- **Capabilities**: Checkout, ProcessPayment
- **Aspects**: Auth, Validation
- **Decisions**: Architecture decisions

## Integration

Auto-Skill uses Mental for:

- Pattern enhancement (domain context)
- Skill suggestions by domain
- Confidence boost for aligned skills
- Auto-generated documentation

## Setup

```bash
npm install -g @mental-model/cli
mental init
mental add domain "Payment"
```

[Learn more →](overview.md)
