# Synapse-Backend/test_qdrant.py (Corrected)

import asyncio
import sys
from pathlib import Path

# --- FIX: Add the project root to the Python path ---
# This ensures that the script can find the 'src' module.
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))
# --- End of FIX ---

from src.services.real.vector_store_service import RealVectorStoreService

async def main():
    """
    A simple script to test the connection to Qdrant and initialize the collection.
    """
    print("--- Testing Qdrant Connection and Initialization ---")
    try:
        # Initialize our vector store service
        vector_service = RealVectorStoreService()
        
        # Call the initialize_store method, which will create the collection
        await vector_service.initialize_store()
        
        # Properly close the client connection
        await vector_service.close()
        
        print("\n--- Test successful! ---")
        print("The 'synapse_memory' collection is ready in Qdrant.")
    except Exception as e:
        print(f"\n--- Test failed with error: {e} ---")

if __name__ == "__main__":
    asyncio.run(main())