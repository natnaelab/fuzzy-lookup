## Nginx / TLS Setup

1. **Point DNS**  
   Create `A` records for `fuzzylookupmatch.com`, `www.fuzzylookupmatch.com`, and `api.fuzzylookupmatch.com` that point to your server.

2. **Obtain certificates**  
   Use Certbot (webroot mode) on the server so it can write challenges into `nginx/certbot`. Example:
   ```bash
   sudo certbot certonly --webroot \
     -w /path/to/repo/nginx/certbot \
     -d fuzzylookupmatch.com -d www.fuzzylookupmatch.com

   sudo certbot certonly --webroot \
     -w /path/to/repo/nginx/certbot \
     -d api.fuzzylookupmatch.com
   ```

3. **Install certs**  
   Copy the resulting `fullchain.pem` and `privkey.pem` into:
   ```
   nginx/ssl/fuzzylookupmatch.com/{fullchain.pem,privkey.pem}
   nginx/ssl/api.fuzzylookupmatch.com/{fullchain.pem,privkey.pem}
   ```

4. **Deploy**  
   Bring the stack up (after setting environment variables):
   ```bash
   docker compose up --build -d
   ```
   Nginx will proxy the SPA to the `frontend` container and the API to `backend`.
