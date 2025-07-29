# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Git Onboard, please send an email to [security@1bitcode.com](mailto:security@1bitcode.com). All security vulnerabilities will be promptly addressed.

### What to include in your report:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** of the vulnerability
- **Suggested fix** (if any)

### Response timeline:

- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Resolution**: As soon as possible, typically within 2 weeks

### Disclosure policy:

- Security vulnerabilities will be disclosed via GitHub Security Advisories
- Patches will be released as soon as possible
- Credit will be given to reporters who wish to be acknowledged

## Security Best Practices

When using Git Onboard:

1. **Keep your SSH keys secure** - Never share your private SSH keys
2. **Use HTTPS for sensitive repositories** - Consider using HTTPS instead of SSH for very sensitive projects
3. **Review .gitignore carefully** - Ensure sensitive files are properly ignored
4. **Update regularly** - Keep Git Onboard updated to the latest version
5. **Monitor logs** - Check the log file for any suspicious activity

## Security Features

Git Onboard includes several security features:

- **No external dependencies** - Reduces attack surface
- **Local processing only** - No data sent to external services
- **Secure file handling** - Proper file permissions and cleanup
- **Input validation** - All user inputs are validated
- **Error handling** - Secure error messages that don't leak sensitive information

## Contact

For security-related issues, please contact:
- Email: [security@1bitcode.com](mailto:security@1bitcode.com)
- GitHub: Create a private security advisory 