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

### Where to Create
1. Go to **Cloudflare Dashboard** → **My Profile** (top right) → **API Tokens**.
2. Click **Create Token** → **Custom Token**.
3. Name it "Visa Deployment Token".

### Permissions to Select
Under **Permissions**, ensure you add ALL of these:

| Permission Group | Access Level | UI Selection Path |
|------------------|--------------|-------------------|
| **Account** | **Workers R2 Storage** | Edit | Account → Workers R2 Storage → Edit |
| **Account** | **Workers KV Storage** | Edit | Account → Workers KV Storage → Edit |
| **Account** | **Workers Scripts** | Edit | Account → Workers Scripts → Edit |
| **Account** | **Workers REST API** | Edit | Account → Workers Pages → Edit (if visible) or All Account Settings |
| **Account** | **Pages** | Edit | Account → Pages → Edit |
| **Account** | **Workers AI** | Read/Run | Account → Workers AI → Read |

*Tip: For "Account" permissions, ensure you select "Include" -> "All accounts" or your specific account.*

---

## 3. How to Setup KV (Key-Value Storage)

### Step 1: Create Namespaces
You need two namespaces. Run these commands in your project root:

```bash
# Production Cache
npx wrangler kv:namespace create "VISA_CACHE"

# Session Storage
npx wrangler kv:namespace create "SESSION"
```

### Step 2: Update `wrangler.toml`
The commands above will output `id` strings (e.g., `id = "209c..."`). Copy these into your `wrangler.toml` file:

```toml
# In wrangler.toml

[[kv_namespaces]]
binding = "VISA_CACHE"
id = "PASTE_VISA_CACHE_ID_HERE"
preview_id = "PASTE_VISA_CACHE_PREVIEW_ID_HERE"

[[kv_namespaces]]
binding = "SESSION"
id = "PASTE_SESSION_ID_HERE"
preview_id = "PASTE_SESSION_PREVIEW_ID_HERE"
```

---

## 4. Required Secrets (Environment Variables)

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
