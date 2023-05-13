import string
import unittest

from ddt import ddt, data, unpack
from syntaxtree.parsedNode import ParsedNode
from structure.token import Token
from structure.tokenTypes import TokenTypes
from syntaxtree.nodes import *
from verse_lexer import lexicon
from verse_parser import Parser
from verse_interpreter import Interpreter

#  @data({'input': 'bla', 'expected': 'res'})

@ddt
class InterpreterTest(unittest.TestCase):
    '''
    Test: Tuple
    '''
    @data({'input': 'z:int; z=7; y:=(31|5); x:=(7|22); (z,x,y)', 'expected': '((7,7,31)|(7,7,5)|(7,22,31)|(7,22,5))'})
    @data({'input': 'x=(y|2); y=(1|3|z:int); x,y:int; t:int; t = (z = 10; 2); (x,y)', 'expected': '((1,1)|(3,3)|(10,10)|(2,1)|(2,3)|(2,10))'})
    @unpack
    def test_tuple(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

    '''
    Test: FOR
    '''
    @data({'input': 'for{1..10}', 'expected': '(1,2,3,4,5,6,7,8,9,10)'})
    @data({'input': 'for{3|4}', 'expected': '(3,4)'})
    @data({'input': 'for{false?}', 'expected': '()'})
    @data({'input': 'for(x:=10|20; x>10; y:=1|2|3; y<3)do(x+y)', 'expected': '(21|22)'}) # <- filtering variables
    @data({'input': 'for(x:=10|20; y:=1|2|3)do(x+y)', 'expected': '(11|12|13|21|22|23)'})
    @data({'input': 'for(x:=2|3|5)do(x+1)', 'expected': '(3|4|6)'})
    # @data({'input': 'for(x:=10|20) do (x | x+1)', 'expected': '((10|20)|(10|21)|(11|20)|(11|21))'})
    @data({'input': 'for(x:=2|3|5; x > 2)do(x+(1|2))', 'expected': '(4|5|6|7)'})
    @data({'input': 't:=(1,1,1); for(i:int;x:=t[i]) do (x+i)', 'expected': '(1,2,3)'}) # <- indexing still work in progress
    @unpack
    def test_for(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)
    
    '''
    Test: IF
    '''
    # @data({'input': 'x:int; x=10; if(x=r:int) then 70 else 30', 'expected': 'false?'})
    @data({'input': 'x,y:int; if(x<20) then y=70 else y=10; x=7; y', 'expected': '70'})
    @data({'input': 'x,y:int; y = (if (x = 0) then 3 else 4); x = 7; y', 'expected': '4'})
    # @data({'input': 'x; x = 10; r=11; if(x = r:int) then (x:int; 1) else 3', 'expected': 'false?'})
    @data({'input': 'x:int; x=10; y:=(if(x=r:int) then 70 else 30); r=10; y', 'expected': '70'})
    @data({'input': 'x,y,p,q:int; if(x=0) then {p=3;q=4} else {p=333;q=444}; x=0; (p,q)', 'expected': '(3,4)'})
    @data({'input': 'x,y,p,q,r:int; if(x=0) then {p = r; r = 10; q=4} else {p=333;q=444}; x=0; (p,q)', 'expected': '(10,4)'})
    @data({'input': 'x,y,p,q:int; if(x=0) then { p = r:int; r = 10; q=4} else {p=333;q=444}; x=0; (p,q)', 'expected': '(10,4)'})
    @data({'input': 'x,y,p,q:int; if(x=0) then { p = r; r=10; r:int; q=4} else {p=333;q=444}; x=0; (p,q)', 'expected': '(10,4)'})
    @unpack
    def test_if(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

    '''
    Test: FUNCTION
    '''    
    @data({'input': 'x:=1; f(x:int):int := (x + 1)', 'expected': '1'})
    # @data({'input': 'x:int; z:int; f(p:int,q:int):int :=  (p = 1; q = 23; y:int; y = 100; (p+q)*100); f(x,z); x + z', 'expected': 'false?'})
    # @data({'input': 'x:int; f(p:int):int :=  (p = 1; y:int; y = 100; (p)*100); f(x); x', 'expected': 'res'})
    # @data({'input': 'f:=(x:int=> d(x) + 1 ); d(p:int):= (p*2); f(3)', 'expected': 'res'})
    @unpack
    def test_function(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

    '''
    Test: CHOICE
    '''
    @data({'input': '1..10', 'expected': '(1|2|3|4|5|6|7|8|9|10)'})
    @data({'input': 'z:int; z=7; y:=(31|5); x:=(7|22); (z,x,y)', 'expected': '((7,7,31)|(7,7,5)|(7,22,31)|(7,22,5))'})
    @data({'input': 'x=(y|2); y=(1|3|z:int); x,y:int; t:int; t = (z = 10; 2); (x,y)', 'expected': '((1,1)|(3,3)|(10,10)|(2,1)|(2,3)|(2,10))'})
    @data({'input': 't:=(10,27,32); x:=(1 | 0 | 1); t[x]', 'expected': '(27,10,27)'})
    @data({'input': 'x:=10|20|15; x<20', 'expected': '(10|15)'})
    @data({'input': 'x,y:int; y = 31|5; x = 7|22; (x,y)', 'expected': '((7,31)|(7,5)|(22,31)|(22,5))'})
    @data({'input': 'x,y:int; x = 7|22; y = 31|5; (x,y)', 'expected': '((7,31)|(22,31)|(7,5)|(22,5))'})
    @data({'input': 'x:int; r=11; t:=(1,(1|(2;3;x)));x = 10; t', 'expected': '((1,1)|(1,10))'})
    @unpack
    def test_choice(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

    '''
    Test: UNIFICATION
    '''    
    @data({'input': 'x:int; x=23; x = 23;  x', 'expected': '23'})
    @data({'input': 'x,y,p,q:int; if(x=0) then { p = r; r=10; p=11; r:int; q=4} else {p=333;q=444}; x=0; (p,q)', 'expected': 'false?'})
    @data({'input': 'x:int; x = (z:int,2); x = (3,y:int,r:int); x', 'expected': 'false?'})
    @data({'input': 'x:int; x = (z:int,2); x = (3,y:int); x', 'expected': '(3,2)'})
    @data({'input': 'x:int; x=23; x = 2;  x', 'expected': 'false?'})
    @data({'input': 'z:=x+y; x,y:int; x=7; y = 3;z', 'expected': '10'})
    @unpack
    def test_unification(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

    '''
    Test: FALSE
    '''    
    @data({'input': 'x:int; x:int; r=11; r:int; r', 'expected': 'false?'})
    @data({'input': 'x:=10; x<7; 3', 'expected': 'false?'})
    @data({'input': 'x,y:int; y= 4; x=y', 'expected': 'false?'})
    @data({'input': 'x:int; x=7; x=3', 'expected': 'false?'})
    @unpack
    def test_false(self, input: string, expected: string):
        self.lexer = lexicon(input)
        self.parser = Parser(self.lexer)
        self.interpreter = Interpreter(self.parser)
        result = self.interpreter.interpret()
        self.assertTrue(repr(result) == expected)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)       