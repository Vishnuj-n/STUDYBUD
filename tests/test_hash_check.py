import pytest
from hash_check import PDFDuplicateChecker

# Sample PDF content (as bytes) for testing
PDF_CONTENT_1 = b"This is a test PDF content."
PDF_CONTENT_2 = b"This is another test PDF content."

@pytest.fixture
def checker():
    """
    Pytest fixture to create a PDFDuplicateChecker instance
    using an in-memory SQLite database for each test.
    """
    # Using ':memory:' creates a temporary in-memory database that is destroyed after the test
    checker_instance = PDFDuplicateChecker(db_path=":memory:")
    # The __enter__ and __exit__ methods on the checker will handle connection setup/teardown
    with checker_instance as chk:
        yield chk

def test_compute_hash(checker):
    """
    Test that the hash computation is correct and consistent.
    """
    hash1 = checker.compute_hash(PDF_CONTENT_1)
    hash2 = checker.compute_hash(PDF_CONTENT_1)
    hash3 = checker.compute_hash(PDF_CONTENT_2)

    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hash length
    assert hash1 == hash2  # Hashes of the same content should be identical
    assert hash1 != hash3  # Hashes of different content should be different

def test_check_new_file(checker):
    """
    Test checking a new file that is not in the database.
    It should be marked as not a duplicate, and the initial concepts list should be empty.
    """
    is_dup, concepts = checker.check_and_store_key_concepts(PDF_CONTENT_1, ["concept1", "concept2"])
    assert not is_dup
    assert concepts == []

def test_check_duplicate_file(checker):
    """
    Test checking a file that has already been added.
    It should be marked as a duplicate, and its stored concepts should be returned.
    """
    # First, add the file to the database (as if it's a new upload)
    checker.check_and_store_key_concepts(PDF_CONTENT_1, [])

    # Now, store some concepts for it
    checker.store_key_concepts(PDF_CONTENT_1, ["conceptA", "conceptB"])

    # Finally, check the file again
    is_dup, concepts = checker.check_and_store_key_concepts(PDF_CONTENT_1, [])
    assert is_dup
    assert concepts == ["conceptA", "conceptB"]

def test_store_and_get_key_concepts(checker):
    """
    Test storing and then retrieving key concepts for a file.
    """
    # First, add the file hash to the DB (as if it was just uploaded)
    checker.check_and_store_key_concepts(PDF_CONTENT_1, [])

    # Now, store concepts for it
    concepts_to_store = ["testing", "storage", "retrieval"]
    checker.store_key_concepts(PDF_CONTENT_1, concepts_to_store)

    # Retrieve the concepts
    retrieved_concepts = checker.get_key_concepts(PDF_CONTENT_1)
    assert retrieved_concepts == concepts_to_store

def test_get_key_concepts_for_unknown_file(checker):
    """
    Test that getting concepts for a file not in the DB returns an empty list.
    """
    retrieved_concepts = checker.get_key_concepts(PDF_CONTENT_1)
    assert retrieved_concepts == []

def test_duplicate_with_no_initial_concepts(checker):
    """
    Test the case where a duplicate is found but it had no concepts stored.
    """
    # Add a file with no concepts
    checker.check_and_store_key_concepts(PDF_CONTENT_1, [])

    # Check it again
    is_dup, concepts = checker.check_and_store_key_concepts(PDF_CONTENT_1, [])
    assert is_dup
    assert concepts == []
