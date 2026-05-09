# Security Policy

## Reporting Security Vulnerabilities

**Please DO NOT open public issues for security vulnerabilities.**

If you discover a security vulnerability in AutoAttendance, please email:

📧 **security@autoattendance.dev**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

## Security Measures

AutoAttendance implements several security features:

### Data Protection
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection
- ✅ CSRF protection
- ✅ Rate limiting

### Authentication & Authorization
- ✅ Environment-based configuration
- ✅ Secure credential handling
- ✅ No hardcoded secrets
- ✅ API key validation (when implemented)

### Database Security
- ✅ SQLite with file permissions
- ✅ Backup integrity verification
- ✅ Data encryption options
- ✅ Audit logging

### Code Quality
- ✅ Regular dependency updates
- ✅ Security scanning (bandit, safety)
- ✅ Code review process
- ✅ Automated testing

## Best Practices for Users

### Deployment Security

1. **Use HTTPS in Production**
   ```bash
   # Use nginx or Apache as reverse proxy with SSL
   ```

2. **Secure Database**
   ```bash
   # Set file permissions
   chmod 600 models/attendance.sqlite3
   ```

3. **Environment Variables**
   ```bash
   # Never commit .env file
   # Use secure secret management
   ```

4. **API Authentication**
   - Enable API key requirement
   - Use JWT tokens
   - Implement rate limiting

5. **Network Security**
   - Use VPN for remote access
   - Firewall rules
   - IP whitelisting

### Password & Credential Management

- ✅ Use strong, unique passwords
- ✅ Never share credentials
- ✅ Rotate keys regularly
- ✅ Use password managers
- ✅ Enable 2FA where possible

### Backup & Recovery

```bash
# Regular backups
python cli.py backup

# Encrypt backups
gpg --encrypt backup.sql

# Test restoration
sqlite3 test.db < backup.sql
```

## Dependencies & Updates

### Checking for Vulnerabilities

```bash
# Install security tools
pip install bandit safety

# Run security checks
bandit -r .
safety check
```

### Updating Dependencies

```bash
# Check for updates
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Test after updates
pytest tests/
```

## Known Issues

None currently reported. If you find a vulnerability, please report it via security@autoattendance.dev

## Security Changelog

### v1.0.0 (Initial Release)
- Input validation implemented
- SQL injection prevention
- Rate limiting added
- Dependency scanning enabled

## Third-Party Security

AutoAttendance uses these security-critical libraries:
- **insightface** - Face recognition model
- **opencv-python** - Computer vision
- **fastapi** - Web framework
- **sqlalchemy** - Database ORM

All dependencies are monitored for security updates.

## Compliance

AutoAttendance aims for compliance with:
- ✅ OWASP Top 10
- ✅ CWE/SANS Top 25
- ✅ NIST Cybersecurity Framework
- 🚧 GDPR (for EU deployments)
- 🚧 CCPA (for US deployments)

## Security Headers

Recommended headers for production:

```
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

---

## Support

For security questions: security@autoattendance.dev
