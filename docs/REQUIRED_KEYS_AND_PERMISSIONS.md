# Required Keys, Permissions, and Resources

To deploy the Visa Platform successfully, ensure you have the following resources created and keys configured.

## 1. Cloudflare Resources (Create Manually)

Run these commands locally or enable them in the Cloudflare Dashboard:

### R2 Buckets (Storage)
The deployment fails if these don't exist.
```bash
wrangler r2 bucket create visa-platform-storage
```

### KV Namespaces (Caching & Sessions)
Create these and update `wrangler.toml` with the IDs.
```bash
wrangler kv:namespace create "VISA_CACHE"
wrangler kv:namespace create "SESSION"
```
*After creating, update the `id` fields in `wrangler.toml` with the generated IDs.*

---

## 2. Cloudflare API Token Permissions

The API Token used for **deployment** (in GitHub Actions or CI/CD) needs the following permissions:

| Permission Group | Access Level | Reason |
|------------------|--------------|--------|
| **Workers Scripts** | Edit | Deploy workers |
| **Workers Pages** | Edit | Deploy Pages/Assets |
| **Workers KV Storage** | Edit | Bind/Write to KV |
| **Workers R2 Storage** | Edit | Bind/Access R2 buckets |
| **Account Settings** | Read | Verify account details |
| **User Details** | Read | Verify user |
| **Workers AI** | Read/Run | Use AI models |

*Note: If you get an error accessing `/r2/buckets/...`, your token likely lacks **Workers R2 Storage** permissions.*

---

## 3. Required Secrets (Environment Variables)

These must be set in your GitHub Repository Secrets or Cloudflare Dashboard (Settings -> Variables).

### For Deployment (CI/CD)
- `CLOUDFLARE_API_TOKEN`: Token with permissions listed above.
- `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID.

### For Application Runtime (Secrets)
Set these using `wrangler secret put <NAME>`:

| Secret Name | Value Description | Used By |
|-------------|-------------------|---------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Application & Workers |
| `SUPABASE_SERVICE_ROLE_KEY` | Your metadata-bypassing generic key | AI/Clustering Workers |
| `CF_ACCOUNT_ID` | Your Cloudflare Account ID | MCP Server / AI Worker |
| `CF_API_TOKEN` | Same as deployment token (or one with AI run permissions) | MCP Server / AI Worker |

---

## 4. Verification Checklist

- [ ] **R2 Bucket** `visa-platform-storage` exists.
- [ ] **KV Namespaces** `VISA_CACHE` and `SESSION` exist and IDs are in `wrangler.toml`.
- [ ] **API Token** has `Workers R2 Storage` Edit permission.
- [ ] **Secrets** are set in Cloudflare (Workers & Pages -> Settings -> Variables).

## Quick Fix for "Bucket Not Found" Error
If specific bucket binding fails, run:
```bash
npx wrangler r2 bucket create visa-platform-storage
```
Then retry deployment.
