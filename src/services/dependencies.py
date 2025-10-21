# In: Synapse-Backend/src/services/dependencies.py

from src.services.interfaces._db import IDatabaseService
from src.services.mocks.mock_db import MockDatabaseService

# This function is our dependency provider.
# Later, you can add logic here to switch between the mock and real service.
def get_db_service() -> IDatabaseService:
    return MockDatabaseService()