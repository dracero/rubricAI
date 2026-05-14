import faiss
import os
import pickle

BASE_PATH = os.getenv("ARETEIA_SYNC_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sync"))



# Global Cache for indices to prevent redundant disk I/O
# Format: { course_id: (index_object, metadata_list) }
_INDEX_CACHE = {}

def get_course_dir(course_id):
    return f"{BASE_PATH}/course_{course_id}"

def get_index_path(course_id):
    return f"{get_course_dir(course_id)}/index.faiss"

def get_metadata_path(course_id):
    return f"{get_course_dir(course_id)}/metadata.pkl"

def save_index(course_id, embeddings, metadata):
    dim = len(embeddings[0])
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    course_dir = get_course_dir(course_id)
    os.makedirs(course_dir, exist_ok=True)
    faiss.write_index(index, get_index_path(course_id))
    with open(get_metadata_path(course_id), "wb") as f:
        pickle.dump(metadata, f)
    
    # Invalidate cache on update
    if course_id in _INDEX_CACHE:
        del _INDEX_CACHE[course_id]

def load_index(course_id):
    """
    Loads index and metadata from disk or cache.
    """
    if course_id in _INDEX_CACHE:
        return _INDEX_CACHE[course_id]

    index_path = get_index_path(course_id)
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index not found for course {course_id}")

    index = faiss.read_index(index_path)
    with open(get_metadata_path(course_id), "rb") as f:
        metadata = pickle.load(f)

    # Store in cache
    _INDEX_CACHE[course_id] = (index, metadata)
    return index, metadata
