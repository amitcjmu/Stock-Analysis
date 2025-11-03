# SSL Certificates for Grafana

**Purpose**: Store SSL certificates for HTTPS access to Grafana

## Files Required

Place the following files in this directory for production HTTPS deployment:

- `grafana.crt` - SSL certificate
- `grafana.key` - Private key

## Local Development (HTTP)

For local development, HTTPS is **optional**. The default configuration uses HTTP:

```bash
# In .env.observability
GF_SERVER_PROTOCOL=http
GF_SERVER_ROOT_URL=http://localhost:9999
```

No SSL certificates are required for local development.

## Azure Production (HTTPS - Recommended)

### Option A: External TLS Termination (Recommended)

Use nginx, Traefik, or Azure App Gateway to terminate TLS **before** Grafana:

```
Internet → Azure App Gateway (HTTPS) → Grafana (HTTP on 9999)
```

**Benefits**:
- Centralized certificate management
- Automatic renewal with Let's Encrypt
- No Grafana configuration needed

**Configuration**:
```bash
# In .env.observability
GF_SERVER_PROTOCOL=http  # Grafana receives HTTP from App Gateway
GF_SERVER_ROOT_URL=https://aiforceasses.cloudsmarthcl.com:9999  # Public URL is HTTPS
```

### Option B: Grafana Native HTTPS

If using Grafana's built-in HTTPS (without external termination):

1. **Obtain Certificates**:
   ```bash
   # From existing Azure Key Vault
   az keyvault secret download --vault-name <vault> --name grafana-cert --file grafana.crt
   az keyvault secret download --vault-name <vault> --name grafana-key --file grafana.key

   # OR generate self-signed (NOT recommended for production)
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout grafana.key -out grafana.crt \
     -subj "/CN=aiforceasses.cloudsmarthcl.com"
   ```

2. **Configure Environment**:
   ```bash
   # In .env.observability
   GF_SERVER_PROTOCOL=https
   GF_SERVER_ROOT_URL=https://aiforceasses.cloudsmarthcl.com:9999
   GF_SERVER_DOMAIN=aiforceasses.cloudsmarthcl.com
   GF_SERVER_CERT_FILE=/etc/grafana/ssl/grafana.crt
   GF_SERVER_CERT_KEY=/etc/grafana/ssl/grafana.key
   ```

3. **Set Permissions**:
   ```bash
   chmod 600 grafana.key
   chmod 644 grafana.crt
   ```

## Railway Production (HTTPS)

Railway provides automatic HTTPS via their platform. No SSL certificates needed:

```bash
# In .env.observability (Railway)
GF_SERVER_PROTOCOL=https
GF_SERVER_ROOT_URL=https://grafana-your-app.railway.app
```

Railway handles TLS termination automatically.

## Security Notes

- **NEVER commit** SSL private keys to git
- `.gitignore` already excludes this directory
- Rotate certificates every 90 days (or use Let's Encrypt)
- Use strong key sizes (2048-bit RSA minimum, 4096-bit recommended)

## Certificate Validation

After placing certificates, verify:

```bash
# Check certificate validity
openssl x509 -in grafana.crt -text -noout

# Check key matches certificate
openssl x509 -noout -modulus -in grafana.crt | openssl md5
openssl rsa -noout -modulus -in grafana.key | openssl md5
# (MD5 hashes should match)

# Test HTTPS connection
curl -k https://localhost:9999/api/health
```

## Troubleshooting

### Certificate Errors

```bash
# Error: "certificate verify failed"
# Fix: Check certificate chain (include intermediate certs)
cat your_domain.crt intermediate.crt root.crt > grafana.crt

# Error: "private key does not match public certificate"
# Fix: Ensure you're using the correct key for the certificate
openssl rsa -noout -modulus -in grafana.key | openssl md5
openssl x509 -noout -modulus -in grafana.crt | openssl md5
```

### Grafana Won't Start

```bash
# Check Grafana logs
docker logs migration_grafana

# Common issues:
# 1. Certificate file not found
ls -la config/docker/observability/ssl/

# 2. Permission denied
docker exec migration_grafana ls -la /etc/grafana/ssl/

# 3. Invalid certificate format
openssl x509 -in grafana.crt -text -noout
```

## References

- ADR-031 (lines 547-551): HTTPS mandatory for production
- Grafana HTTPS Documentation: https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-server-side-tls/
- Let's Encrypt: https://letsencrypt.org/
