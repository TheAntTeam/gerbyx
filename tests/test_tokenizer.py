"""Tests for tokenizer module"""

import pytest
from gerbyx.tokenizer import tokenize_gerber


class TestTokenizer:
    """Test suite for Gerber tokenizer"""
    
    def test_tokenize_simple_param(self):
        """Test tokenization of simple parameter block"""
        gerber = "%FSLAX24Y24*%"
        tokens = list(tokenize_gerber(gerber))
        
        assert len(tokens) == 1
        assert tokens[0] == ('param', 'FSLAX24Y24*')
    
    def test_tokenize_multiple_params(self):
        """Test tokenization of multiple parameters"""
        gerber = "%FSLAX24Y24*MOMM*%"
        tokens = list(tokenize_gerber(gerber))
        
        assert len(tokens) == 2
        assert tokens[0] == ('param', 'FSLAX24Y24*')
        assert tokens[1] == ('param', 'MOMM*')
    
    def test_tokenize_statement(self):
        """Test tokenization of statement"""
        gerber = "D10*"
        tokens = list(tokenize_gerber(gerber))
        
        assert len(tokens) == 1
        assert tokens[0] == ('stmt', 'D10*')
    
    def test_tokenize_comment_g04(self):
        """Test tokenization of G04 comment"""
        gerber = "G04 This is a comment*"
        tokens = list(tokenize_gerber(gerber))
        
        assert len(tokens) == 1
        assert tokens[0] == ('comment', 'G04 This is a comment*')
    
    def test_tokenize_hash_comment(self):
        """Test tokenization with # comments (X3)"""
        gerber = "%FSLAX24Y24*%  # This is a comment"
        tokens = list(tokenize_gerber(gerber))
        
        # Comment should be removed
        assert len(tokens) == 1
        assert tokens[0] == ('param', 'FSLAX24Y24*')
    
    def test_tokenize_mixed_content(self, simple_gerber):
        """Test tokenization of mixed content"""
        tokens = list(tokenize_gerber(simple_gerber))
        
        # Should have params and statements
        param_count = sum(1 for kind, _ in tokens if kind == 'param')
        stmt_count = sum(1 for kind, _ in tokens if kind == 'stmt')
        
        assert param_count > 0
        assert stmt_count > 0
    
    def test_tokenize_multiline_statement(self):
        """Test tokenization of multiline statement"""
        gerber = "X10000\nY10000D03*"
        tokens = list(tokenize_gerber(gerber))
        
        # Should be combined into single statement
        assert len(tokens) == 1
        assert 'X10000' in tokens[0][1]
        assert 'Y10000' in tokens[0][1]
    
    def test_tokenize_empty_string(self):
        """Test tokenization of empty string"""
        tokens = list(tokenize_gerber(""))
        assert len(tokens) == 0
    
    def test_tokenize_whitespace_only(self):
        """Test tokenization of whitespace only"""
        tokens = list(tokenize_gerber("   \n\n  \t  "))
        assert len(tokens) == 0
    
    def test_tokenize_unclosed_param_block(self):
        """Test tokenization of unclosed parameter block"""
        gerber = "%FSLAX24Y24*"
        tokens = list(tokenize_gerber(gerber))
        
        # Should handle gracefully
        assert len(tokens) >= 1
    
    def test_tokenize_macro_definition(self, gerber_with_macro):
        """Test tokenization of macro definition"""
        tokens = list(tokenize_gerber(gerber_with_macro))
        
        # Should contain macro start and primitives
        token_values = [val for _, val in tokens]
        assert any('AMHEXAGON' in val for val in token_values)
    
    def test_tokenize_preserves_asterisks(self):
        """Test that asterisks are preserved in tokens"""
        gerber = "%FSLAX24Y24*%"
        tokens = list(tokenize_gerber(gerber))
        
        assert tokens[0][1].endswith('*')
    
    def test_tokenize_inline_comment_after_command(self):
        """Test inline comment after command (X3)"""
        gerber = "D10*  # Select aperture"
        tokens = list(tokenize_gerber(gerber))
        
        # Comment should be removed
        assert len(tokens) == 1
        assert tokens[0] == ('stmt', 'D10*')
