# test_script.py
"""
Script to test the string_operations module.
"""

# Import the module we created
import string_operations

# Alternatively, you can import specific functions:
# from string_operations import reverse_string, count_vowels, is_palindrome

def main():
    """Main function to test all string operations."""
    
    print("=" * 60)
    print("TESTING STRING OPERATIONS MODULE")
    print("=" * 60)
    
    # Test 1: Reverse String
    print("\n1. TESTING REVERSE STRING:")
    print("-" * 40)
    test_strings = ["hello", "Python", "12345", "A man a plan a canal Panama"]
    
    for s in test_strings:
        reversed_s = string_operations.reverse_string(s)
        print(f"Original: '{s}'")
        print(f"Reversed: '{reversed_s}'")
        print()
    
    # Test 2: Count Vowels
    print("\n2. TESTING COUNT VOWELS:")
    print("-" * 40)
    test_strings = ["hello", "Python", "aeiou", "bcdfg", "Beautiful"]
    
    for s in test_strings:
        vowel_count = string_operations.count_vowels(s)
        print(f"String: '{s}' → Vowels: {vowel_count}")
    
    # Test 3: Check Palindromes
    print("\n\n3. TESTING PALINDROME CHECKER:")
    print("-" * 40)
    test_strings = ["racecar", "hello", "madam", "A man a plan a canal Panama", 
                    "noon", "python", "level"]
    
    for s in test_strings:
        is_palin = string_operations.is_palindrome(s)
        result = "✓ IS a palindrome" if is_palin else "✗ NOT a palindrome"
        print(f"'{s}' → {result}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)


# Run the tests when script is executed
main()