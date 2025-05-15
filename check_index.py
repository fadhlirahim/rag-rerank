import os
from dotenv import load_dotenv
import pinecone

# Load environment variables
load_dotenv(override=True)

# Get Pinecone credentials from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Connect to index
index = pc.Index(PINECONE_INDEX_NAME)

# Get index stats
stats = index.describe_index_stats()

print(f"Index name: {PINECONE_INDEX_NAME}")
print(f"Index stats: {stats}")
print(f"Total vector count: {stats.get('total_vector_count', 'N/A')}")
print(f"Namespaces: {stats.get('namespaces', 'N/A')}")

# List all namespaces
if stats.get('namespaces'):
    for ns, ns_stats in stats['namespaces'].items():
        print(f"Namespace: {ns}, Vector count: {ns_stats.get('vector_count', 'N/A')}")
else:
    print("No namespaces found.")