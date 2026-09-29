def linear_search(records, target_id):
    """Check records one by one until the id matches. O(n)."""
    for record in records:
        if record["id"] == target_id:
            return record
    return None


def build_index(records):
    """Turn the list into a dict keyed by id (done once)."""
    return {record["id"]: record for record in records}


def dict_lookup(index, target_id):
    """Jump straight to the record using the hash table. O(1)."""
    return index.get(target_id)