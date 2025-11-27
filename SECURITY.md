# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Spermophilus, please **do not** open a public GitHub issue. Instead, please email your findings to the maintainers with:

- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if you have one)

We take all security concerns seriously and will work to address them promptly.

## Security Best Practices for Users

When deploying Spermophilus:

1. **Never commit `.env` files** containing real tokens to version control
2. **Use environment variables** for all sensitive data (bot tokens, API endpoints)
3. **Restrict bot access** via `ALLOWED_USER_IDS` - only add trusted users
4. **Run LM Studio locally** or on a secure private network
5. **Monitor logs** for unauthorized access attempts
6. **Keep dependencies updated** by running `uv sync` regularly
7. **Use strong user IDs** from Telegram when configuring `ALLOWED_USER_IDS`

## Known Limitations

- The bot processes files in memory and temporarily stores them in `data/temp/`
- PDF processing requires trusted inputs (no validation of PDF structure)
- External API endpoint (if configured) receives extracted text unencrypted over HTTP

## Security Considerations

- **File uploads**: All files are processed locally. No data leaves your system unless you configure `RESULTS_API_ENDPOINT`
- **Database**: SQLite database stores job history and cached results. Restrict access to the `data/` directory
- **Network**: LM Studio endpoint should not be exposed to untrusted networks
