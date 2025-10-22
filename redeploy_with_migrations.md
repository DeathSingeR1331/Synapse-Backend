# How to Fix the Database Migration Issue

## The Problem

Your Railway deployment is missing the `users` table, causing OAuth authentication to fail with the error:

```
relation "users" does not exist
```

## The Solution

The migrations need to be run on your Railway deployment. Here are the steps:

### Option 1: Redeploy (Recommended)

1. **Go to your Railway dashboard**
2. **Find your Synapse-Backend service**
3. **Click "Deploy" or "Redeploy"** to trigger a new deployment
4. **Watch the deployment logs** to ensure migrations run successfully
5. **Look for these log messages:**
   ```
   Starting migrations...
   Migrations completed successfully!
   ```

### Option 2: Manual Migration (If redeploy doesn't work)

1. **Install Railway CLI:**

   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**

   ```bash
   railway login
   ```

3. **Connect to your project:**

   ```bash
   railway link
   ```

4. **Run migrations manually:**
   ```bash
   railway run alembic upgrade head
   ```

### Option 3: Check Current Migration Status

1. **Check what migrations have been applied:**

   ```bash
   railway run alembic current
   ```

2. **Check migration history:**
   ```bash
   railway run alembic history
   ```

## What Should Happen

After running migrations, you should see these tables created:

- `users` (with columns: uuid, username, email, hashed_password, google_provider_id, etc.)
- `sessions`
- `conversations`
- `chat_messages`
- `conversation_summaries`
- And other related tables

## Verification

Once migrations are complete:

1. **Try the OAuth login again**
2. **Check the Railway logs** for any remaining errors
3. **The frontend should no longer show the oauth_error**

## If Issues Persist

If you still see errors after running migrations:

1. **Check the Railway logs** for specific error messages
2. **Verify environment variables** are set correctly in Railway
3. **Ensure the database connection** is working properly

The key issue is that your production database is missing the required tables that your application expects to exist.
