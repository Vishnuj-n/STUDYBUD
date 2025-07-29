from stringextractor import StringExtractor

def test_extract_list_from_string_with_numbers():
    """
    Tests that the extractor correctly parses a numbered list string.
    """
    extractor = StringExtractor()
    input_string = "1. First item. 2. Second item. 3. Third item."
    expected_output = ["First item", "Second item", "Third item"]
    assert extractor.extract_list_from_string(input_string) == expected_output

def test_extract_list_from_string_with_hyphens():
    """
    Tests that the extractor correctly parses a hyphenated list string.
    """
    extractor = StringExtractor()
    input_string = "- First item\n- Second item\n- Third item"
    expected_output = ["First item", "Second item", "Third item"]
    assert extractor.extract_list_from_string(input_string) == expected_output

def test_extract_list_from_string_empty():
    """
    Tests that the extractor returns an empty list for an empty string.
    """
    extractor = StringExtractor()
    input_string = ""
    expected_output = []
    assert extractor.extract_list_from_string(input_string) == expected_output

def test_extract_list_from_string_no_list():
    """
    Tests that the extractor returns an empty list for a string without list markers.
    """
    extractor = StringExtractor()
    input_string = "Just a regular sentence."
    expected_output = []
    assert extractor.extract_list_from_string(input_string) == expected_output

def test_extract_list_from_string_mixed_and_messy():
    """
    Tests that the extractor can handle a messy string with mixed markers.
    """
    extractor = StringExtractor()
    input_string = "  1. First item.  - Second item... 3. Third item!"
    expected_output = ["First item", "Second item", "Third item!"]
    assert extractor.extract_list_from_string(input_string) == expected_output
