# Manual Migration Guide (Backup Solution)

If the Dockerfile migrations don't work, use this manual approach:

## Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

## Step 2: Login to Railway

```bash
railway login
```

## Step 3: Link to Your Project

```bash
railway link
```

## Step 4: Run Migrations Manually

```bash
railway run alembic upgrade head
```

## Step 5: Verify Tables Created

```bash
railway run python -c "
import asyncio
from src.db.database import AsyncSessionFactory
from src.db.models import User

async def check_tables():
    async with AsyncSessionFactory() as session:
        result = await session.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')
        tables = [row[0] for row in result]
        print('Tables in database:', tables)
        if 'users' in tables:
            print('✅ Users table exists!')
        else:
            print('❌ Users table missing!')

asyncio.run(check_tables())
"
```

## Step 6: Test OAuth

After migrations complete, try logging in again through your frontend.

## If Manual Migration Fails:

1. Check Railway environment variables are set correctly
2. Verify database connection is working
3. Check if there are any permission issues
4. Look at Railway logs for specific error messages
