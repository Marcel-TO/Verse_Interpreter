import copy
from structure.token.token import Token
from structure.tokenTypes.tokenTypes import TokenTypes
from syntaxtree.symboltable.symboltable import SymbolTable
from syntaxtree.sequentor.sequentor import Sequentor
from syntaxtree.identifier_creator.identifier_creator import IdentifierCreator

'''
Top class of all nodes.
'''
class BaseNode:
    def __init__(self, token) -> None:
        self.token = token 

    def visit(self, symboltable: SymbolTable):
        return FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value)) 

    def getChildNodes(self):
        return [FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value))]
    
    def App_Beta(self,identifierFrom, identifierTo):
        pass

#Class that takes a parsed node, containes information if node could have been parsed
class ParsedNode:
    def __init__(self, node: BaseNode, hasSyntaxError:bool ):
        self.node = node
        self.hasSyntaxError = hasSyntaxError

     
'''
Node for block statements.
'''  
class BlockNode(BaseNode):
    def __init__(self, nodes:list[BaseNode]) -> None:
        self.nodes:list[BaseNode] = nodes
        self.seperator = ";"

    def __repr__(self) -> str:    
        return self.seperator.join([repr(n) for n in self.nodes])
    
    def visit(self, symboltable: SymbolTable):
        results = []
        i = 0
        for n in self.nodes:
            result = n.visit(symboltable)
            if result != None:
                #if result.token.type == TokenTypes.IDENTIFIER:
                #    self.nodes[i] = result
                #if result.token.type == TokenTypes.FAIL:
                    #return result
                results.append(result)
            i += 1

        i = 0
        hasFailed = False
        for i in range(len(symboltable.symboltable)):
            hasFailed = False
            results = []
            if symboltable.checkAllUnificationValid() == False:
                return FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value))
            for n in self.nodes:
                result = n.visit(symboltable)
                symboltable.remove_all_except_self()
                if result != None:
                    try:
                        if result.token.type == TokenTypes.FAIL:
                            hasFailed = True
                    except: 
                        pass
                    results.append(result)
            i += 1
        
        '''
        HIER GEÄNDERT Block Node, darf nur ein Value liefern.
        Bsp. y:= (31|(z:=9; z)); x:=(7|22); (x,y)
        wenn er in diesem Block (z:=9; z) die liste übergibt kommt es später zu einem error.
        Er muss das z zurückgeben, sprich Ein resultat vom Block. 
        '''

        if hasFailed:
            return FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value))
        return results[len(results)-1] 

    def getChildNodes(self):
        childNodes = []
        for n in self.nodes:
           childNodes.extend(n.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        for n in self.nodes:
            n.App_Beta(identifierFrom,identifierTo)
'''
Top Node in tree.
''' 
class ProgramNode(BaseNode):
    def __init__(self, node:BlockNode) -> None:
        self.node = node
    
    def visit(self, symboltable: SymbolTable):
        return self.node.visit(symboltable) 
    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.node.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.node.App_Beta(identifierFrom,identifierTo)


'''
Node for binded identifiers.
''' 
class BindingNode(BaseNode):
    def __init__(self,token:Token, leftNode:BaseNode, rightNode:BaseNode) -> None:
        super().__init__(token)
        self.leftNode = leftNode
        self.rightNode = rightNode

    def __repr__(self) -> str:    
        return "{}:={}".format(repr(self.leftNode),repr(self.rightNode))  
    
    def visit(self, symboltable: SymbolTable):
        symboltable.addBinding(self.leftNode.token.value, self.rightNode, None)
        return self.rightNode
    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.leftNode.getChildNodes())
        childNodes.extend(self.rightNode.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.leftNode.App_Beta(identifierFrom,identifierTo)
        self.rightNode.App_Beta(identifierFrom,identifierTo)


'''
Node representing a number.
''' 
class NumberNode(BaseNode):
    def __init__(self, token:Token) -> None:
        super().__init__(token)
        self.value = token.value

    def __repr__(self) -> str:
        return str(self.value)
    
    def visit(self, symboltable: SymbolTable):
        return NumberNode(self.token)

    def getChildNodes(self):
        childNodes = [self]
        return childNodes 

'''
Node representing a string.
''' 
class StringNode(BaseNode):
    def __init__(self, token) -> None:
        super().__init__(token)

    def __repr__(self) -> str:
        return self.token.value
        
    def visit(self, symboltable: SymbolTable):
        return StringNode(self.token)


'''
Operators: +, *, -, /, <, >, <=, >=.

Fail condition on using following nodes for any 
of the above listed operations: FaileNode, SequenceNodes (Except choices).

Operator node, checks its left and right node by visiting it.
Then in the sequentor it get combination if there is or are many choices
in the left and right node. Iterates the sequences received by the sequentor and
return a new node number node or choice node.
'''
class OperatorNode(BaseNode):
    def __init__(self, token:Token, leftNode: BaseNode, rightNode: BaseNode) -> None:
        super().__init__(token)
        self.leftNode = leftNode
        self.rightNode = rightNode

    def __repr__(self) -> str:    
        return "({}) {} ({})".format(repr(self.leftNode),self.token.value,repr(self.rightNode))  

    def visit(self, symboltable: SymbolTable):
        fail_conditions = [TokenTypes.FAIL, TokenTypes.TUPLE_TYPE, TokenTypes.ARRAY_TYPE]

        node_left = self.leftNode.visit(symboltable).visit(symboltable)
        if node_left.token.type in fail_conditions:
                return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
       
        node_right = self.rightNode.visit(symboltable).visit(symboltable)
        if node_right.token.type in fail_conditions:
                return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))

        sequentor = Sequentor([node_left,node_right])
        sequences = sequentor.getSequences()

        # If lenght is one, it can only be two integers.
        if len(sequences) == 1:
            for s in sequences:
                if s[0].token.type == TokenTypes.IDENTIFIER or s[1].token.type == TokenTypes.IDENTIFIER:
                    return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
            # checks if the sequences are string or not
            if s[0].token.type == TokenTypes.STRING or s[1].token.type == TokenTypes.STRING:
                return self.doOperationStr(sequences[0][0].token.value,sequences[0][1].token.value, self.token)
            return self.doOperationInt(sequences[0][0].value,sequences[0][1].value, self.token)
        
        # Else left or/and right node of operation had to be a choice.
        nodes = []
        for s in sequences:
            left_val = s[0]
            right_val = s[1]

            '''
            Checks if left_val or right_val (nodes) are valid for the operation.
            If node save fail node in nodes
            '''
            if (left_val.token.type in fail_conditions) or (right_val.token.type in fail_conditions):
                nodes.append( FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)))
           
            # Else save vale of done operation of left_val and right_val (nodes) into the nodes list.
            else: 
                if left_val.token.type == TokenTypes.STRING or right_val.token.type == TokenTypes.STRING:
                    nodes.append(self.doOperationStr(left_val.token.value, right_val.token.value, self.token))
                    continue
                nodes.append(self.doOperationInt(left_val.value,right_val.value, self.token))

        # creates the choice
        choice = ChoiceSequenceNode(Token(TokenTypes.CHOICE,TokenTypes.CHOICE.value), nodes)

        '''
        Last visit if choice contains for example (false?|false?).
        in the choice visit method it returns only the values without the false?.
        If there are no valid nodes/values in the choice sequence, it return FailNode.
        ''' 
        return choice.visit(symboltable) 
    
    '''
    Does any of the following operations in the match case
    for two values and returns a new node.
    '''
    def doOperationInt(self,val1:int,val2:int, token:Token):
        result = 0
        if token.type == TokenTypes.DIVIDE:
            result = val1 // val2
        elif token.type == TokenTypes.MULTIPLY:
            result = val1 * val2
        elif token.type == TokenTypes.PLUS:
            # APPLICATION: add⟨k1, k2⟩ −→ k3      
            result = val1 + val2
        elif token.type == TokenTypes.MINUS:
            result = val1 - val2
        # APPLICATION: gt⟨k1, k2⟩ −→ k1  &  gt⟨k1, k2⟩ −→ fail
        elif token.type == TokenTypes.GREATER:
            if val1 > val2:
                result = val1
            else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.GREATEREQ:
            if val1 >= val2:
                result = val1
            else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.LOWER:
                if val1 < val2:
                    result = val1
                else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.LOWEREQ:
                if val1 <= val2:
                    result = val1
                else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        return  NumberNode(Token(TokenTypes.INTEGER, result))  
    
    def doOperationStr(self, val1: str, val2: str, token: Token):
        result = ""
        if token.type == TokenTypes.PLUS:
            result = val1 + val2
        # APPLICATION: gt⟨k1, k2⟩ −→ k1  &  gt⟨k1, k2⟩ −→ fail
        elif token.type == TokenTypes.GREATER:
            if val1 > val2:
                result = val1
            else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.GREATEREQ:
            if val1 >= val2:
                result = val1
            else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.LOWER:
                if val1 < val2:
                    result = val1
                else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        elif token.type == TokenTypes.LOWEREQ:
                if val1 <= val2:
                    result = val1
                else: return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value)) 
        return StringNode(Token(TokenTypes.STRING, result))
    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.leftNode.getChildNodes())
        childNodes.extend(self.rightNode.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.leftNode.App_Beta(identifierFrom,identifierTo)
        self.rightNode.App_Beta(identifierFrom,identifierTo)

'''
If unary node is called, it calls visitor operator in following way:
creates multiplication operator node containg -1 and its val it has to multiply.
'''
class UnaryNode(BaseNode):
    def __init__(self, token:Token, node) -> None:
        super().__init__(token)
        self.node = node

    def __repr__(self) -> str:    
        return "{}{}".format(self.token.value,repr(self.node)) 

    def visit(self, symboltable: SymbolTable):
        mul:int = 1
        if self.token.type == TokenTypes.MINUS:
            mul = -1
        res = OperatorNode(Token(TokenTypes.MULTIPLY, TokenTypes.MULTIPLY.value),
                                                 NumberNode(Token(TokenTypes.INTEGER,mul)),self.node)
        return res.visit(symboltable)

    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.node.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.node.App_Beta(identifierFrom,identifierTo)
             

'''
Node for identifiers.
''' 

class IdentifierNode(BaseNode):
    def __init__(self, token:Token) -> None: #Change into Variable/IdentifierNode
        super().__init__(token)

    def __repr__(self) -> str:
        return str(self.token.value)

    def visit(self, symboltable: SymbolTable):
        # checks if the identifier already exists in the scopetable.
        (isValid, result) = symboltable.get_value(self.token.value)
        if isValid and result != None:
            return result.visit(symboltable)
        if symboltable.parentTable != None:
            (isValid, result) = symboltable.parentTable.get_value(self.token.value)
            if isValid and result != None:
                return result.visit(symboltable)
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
    
    def getChildNodes(self):
        childNodes = [self]
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        if(self.token.value == identifierFrom):
            self.token.value = identifierTo

'''
Node for scoped identifiers.
''' 
class ScopeNode(BaseNode):
    def __init__(self, token:Token, nodes:list[BaseNode], type) -> None: #Change into Variable/IdentifierNode
        super().__init__(token)
        self.nodes = nodes
        self.type = type
        self.seperator = ","
        self.isVisitted: bool = False

    def __repr__(self) -> str:    
        return "{}{}{}".format(self.seperator.join([repr(n) for n in self.nodes]),self.token.value, repr(self.type)) 

    def visit(self, symboltable: SymbolTable):
        
        for n in self.nodes:

            isValid = symboltable.addScope(n.token.value, self.type.visit(symboltable))
            
            if isValid == False and self.isVisitted == False:
                return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
            else: self.isVisitted = True
                   
        return self.nodes[0]
    
    def getChildNodes(self):
        childNodes = self.nodes
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        for n in self.nodes:
            n.App_Beta(identifierFrom, identifierTo)
        

'''
Top class node for types (int, tuple, etc.).
''' 
class TypeNode(BaseNode):
    def __init__(self, token:Token) -> None: 
        super().__init__(token)
        self.type = type

    def __repr__(self) -> str:
        return str(self.token.value)

    def visit(self, symboltable: SymbolTable):
        return self.token.type 

    def getChildNodes(self):
        childNodes = [self]
        return childNodes

'''
Node for sequence types (tuple).
''' 
class SequenceTypeNode(TypeNode):
    def __init__(self, token:Token, types:list[TypeNode]) -> None: 
        super().__init__(token)
        self.types = types
        self.seperator = ","

    def __repr__(self) -> str:
        if(self.token.type == TokenTypes.TUPLE_TYPE):
            return "tuple({})".format(self.seperator.join([repr(t) for t in self.types]))
        return "array{{}}".format(self.seperator.join([repr(t) for t in self.types]))

    def visit(self, symboltable: SymbolTable):
        result = []
        for n in self.types:
            result.append(n.visit(symboltable))
        return result 
    
    def getChildNodes(self):
        childNodes = []
        for t in self.types:
            childNodes.extend(t.getChildNodes())
        return childNodes

'''
Node for scoped func calls.
''' 
class FuncCallNode:
    def __init__(self,identifier:IdentifierNode, args:list) -> None:
        self.identifier = identifier
        self.args = args

    def visit(self, symboltable: SymbolTable):
        table = symboltable.createChildTable()
        (isValid, result) = symboltable.get_value(self.identifier.token.value)
            
        if isValid:
            try:
                # checks if it is not a func call but a data call instead
                if result.type.token.type == TokenTypes.DATA:
                    return result.setParam(self.args)
            except: 
                pass
            
            func_dec:FuncDeclNode = result
            index = 0
            params = func_dec.params
            for param in params:
                id = param.nodes[0].token.value

                arg = self.args[index].visit(symboltable)
                if(arg.token.type == TokenTypes.IDENTIFIER):
                     arg = None

                table.addBinding(id, arg ,param.type)
                index += 1
            val = func_dec.block.visit(table)

            # Check if a variable is given to argument that has not been set (Logic)
            index = 0
            for arg in self.args:
                 if arg.token.type == TokenTypes.IDENTIFIER:  
                    arg = arg.token.value            
                    id = params[index].nodes[0].token.value
                    param_val_at_arg_pos = table.get_value(id)
                    if param_val_at_arg_pos[0]:
                        symboltable.addValue(arg, param_val_at_arg_pos[1])
                 index += 1
            return val
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        
    def getChildNodes(self):
        childNodes = []
        for arg in self.args:
            childNodes.extend(arg.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        for arg in self.args:
            arg.App_Beta(identifierFrom, identifierTo)

'''
Node for func declarations.
''' 
class FuncDeclNode:
    def __init__(self,identifier:IdentifierNode, params:list[ScopeNode],usesLambda:bool, type:TypeNode, block:BlockNode) -> None:
        self.identifier = identifier
        self.params = params
        self.usesLambda = usesLambda
        self.type = type
        self.block = block

    def visit(self, symboltable: SymbolTable):
        symbol = self.identifier.token.value
        symboltable.addBinding(symbol, self, self.type)

    def getChildNodes(self):
        childNodes = []
        for param in self.params:
            childNodes.extend(param.getChildNodes()) 
        childNodes.extend(self.block.getChildNodes())
        return childNodes


'''
Node for scoped data calls.
''' 
class DataCallNode:
    def __init__(self,identifier:IdentifierNode, param:BaseNode) -> None:
        self.identifier = identifier
        self.param = param

    def visit(self, symboltable: SymbolTable):
        table = symboltable.createChildTable()
        # Change that DataDecl is returned"
        (isValid, value) = symboltable.get_value(self.identifier.token.value)

        if isValid == False:
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        
        result = value.visit(symboltable)
        
        return result.getParam(self.param)


'''
Node for data declarations.
''' 
class DataDeclNode:
    def __init__(self,identifier:IdentifierNode, params:list[ScopeNode], type:BaseNode, block: BlockNode) -> None:
        self.identifier = identifier
        self.params = params
        self.type = type
        self.block = block
        self.symboltable_params = SymbolTable(None)
    
    def __init__(self,identifier:IdentifierNode, params:list[ScopeNode], type:BaseNode) -> None:
        self.identifier = identifier
        self.params = params
        self.type = type
        self.symboltable_params = SymbolTable(None)

    def visit(self, symboltable: SymbolTable):
        self.symboltable_params = symboltable.createChildTable()
        for param in self.params:
            param.visit(self.symboltable_params)
        symboltable.addBinding(self.identifier.token.value, self, self.type.visit(symboltable))
    
    def setParam(self, args: list[BaseNode]):
        if len(self.params) != len(args):
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        try:
            for i in range(0, len(self.params)):
                for node in self.params[i].nodes:
                    self.symboltable_params.addValue(node.token.value, args[i])
        except:
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        return self
    
    def getParam(self, param: BaseNode):
        (isValid, result) = self.symboltable_params.get_value(param.token.value)
        if isValid and result != None:
            return result.visit(self.symboltable_params)
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
    
    def getChildNodes(self):
        childNodes = []
        for param in self.params:
            childNodes.extend(param.getChildNodes()) 
        childNodes.extend(self.block.getChildNodes())
        return childNodes


'''
Node for loops.
''' 
class ForNode(BaseNode):
    def __init__(self, token:Token, node: BaseNode, do: BaseNode) -> None:
        super().__init__(token)
        self.node = node
        self.do = do

    def visit(self, symboltable: SymbolTable):
        if self.do == None:
            return self.visit_curly(self.node.visit(symboltable))

        for_table = symboltable.createChildTable()
        isIndexing = False
        isBinding = False
        indexingNode = None

        # check if block or not
        try: 
            for n in self.node.nodes:
                # checks if there are filter options for the block
                if self.check_type(n.token.type, [TokenTypes.LOWER, TokenTypes.LOWEREQ, TokenTypes.GREATER, TokenTypes.GREATEREQ]):
                    result = n.visit(for_table)
                    for_table.change_value(n.leftNode.token.value, result)
                    continue
                # checks if there could be an indexing node in a binding/flex_eq
                if self.check_type(n.token.type, [TokenTypes.BINDING, TokenTypes.EQUAL]):
                    if self.check_type(n.rightNode.token.type, [TokenTypes.SBL]):
                        isIndexing = True
                        indexingNode = n
                        isBinding = True
                # checks if there is an indexing node
                if self.check_type(n.token.type, [TokenTypes.SBL]):
                    isIndexing = True
                    indexingNode = n
                result = n.visit(for_table)
        except:
            result = self.node.visit(for_table)
        
        # checks if there was an indexing node in the block
        if isIndexing:
            if isBinding:
                return self.for_indexing_binding(for_table, indexingNode)
            return self.for_indexing(symboltable, indexingNode)
        result = self.execDo(for_table)
        return self.convert(result,for_table)
    
    def getChildNodes(self):
        childNodes = []

        childNodes.extend(self.node.getChildNodes()) 
        childNodes.extend(self.do.getChildNodes())
        return childNodes
    
    def visit_curly(self, result: BaseNode):
        # returns converted choice into tuple
        if self.check_type(result.token.type, [TokenTypes.COMMA, TokenTypes.CHOICE]):
            return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), result.nodes)

        # returns single tuple
        if self.check_type(result.token.type, [TokenTypes.INTEGER]):
            return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), [result.token.value])

        # returns empty tuple
        if self.check_type(result.token.type, [TokenTypes.FAIL]):
            return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), [])
    
    def for_indexing_binding(self, symboltable: SymbolTable, indexingNode: BaseNode):
        # checks if the value contains already a value
        (isValid, result) = symboltable.get_value(indexingNode.rightNode.index.token.value)
        results = []
        tuple = indexingNode.rightNode.identifier.visit(symboltable)
        # checks if the symbol exists in table but has no value -> z.B for(i:int; t[i])....
        if isValid and result == None:
            for i in range(0, len(tuple.nodes)):
                # iterates through nodes, overwrites current value and create tuple with results
                symboltable.change_value(indexingNode.leftNode.token.value, tuple.nodes[i])
                symboltable.change_value(indexingNode.rightNode.index.token.value, NumberNode(Token(TokenTypes.INTEGER, i)))
                results.append(self.do.visit(symboltable))
            return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), results)
        # iterates through each node and gets tuple
        for i in range(0, len(tuple.nodes)):
            results.append(self.do.visit(symboltable))
        return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), results)

    def for_indexing(self, symboltable: SymbolTable, indexingNode: BaseNode):
        # checks if the value contains already a value
        (isValid, result) = symboltable.get_value(indexingNode.index.token.value)
        results = []
        tuple = indexingNode.identifier.visit(symboltable)
        # iterates through each node and gets tuple
        for i in range(0, len(tuple.nodes)):
            results.append(self.do.visit(symboltable))
        return SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), results)
    
    def execDo(self, symboltable: SymbolTable):
        try:
            result =  self.do.visit(symboltable)
        except:
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        return result

    def getChildNodes(self):
        childNodes = []
        for param in self.params:
            childNodes.extend(param.getChildNodes())
        return childNodes
    
    def convert(self,result,symboltable):
        if result.token.type == TokenTypes.CHOICE:
            result = SequenceNode(Token(TokenTypes.TUPLE_TYPE, TokenTypes.TUPLE_TYPE.value), result.nodes)
            result = result.visit(symboltable)
        return result
    
    # checks if a type exists in the following type list.
    def check_type(self,type:TokenTypes,types:list[TokenTypes]) -> bool:
        return type in types

    def App_Beta(self,identifierFrom, identifierTo):
        self.node.App_Beta(identifierFrom, identifierTo)
        self.do.App_Beta(identifierFrom, identifierTo)
'''
Node for if statements.
''' 
class IfNode(BaseNode):
    def __init__(self, token:Token, if_node: BaseNode, then_node: BaseNode, else_node: BaseNode) -> None:
        super().__init__(token)
        self.if_node = if_node
        self.then_node = then_node
        self.else_node = else_node

    def __repr__(self) -> str:    
        return "{}({}) then {} else {}".format(self.token.value, repr(self.if_node), repr(self.then_node),  repr(self.else_node))

    def visit(self, symboltable: SymbolTable):
        # x = 10; r=11; if(x = r:int) then (x:int; 1) else (x:int; 3)

        result_if = self.if_node.visit(symboltable)
        if result_if != None and result_if.token.type != TokenTypes.FAIL:
            result_then = self.then_node.visit(symboltable)
            if self.check_type(result_then.token.type, [TokenTypes.TUPLE_TYPE, TokenTypes.CHOICE]):
                return result_then.nodes[0]
            return result_then
            
            
        if_symboltable = symboltable.createChildTable()
        result = self.else_node.visit(if_symboltable)
        for i in range(0, len(if_symboltable.symboltable)):
               result =  self.else_node.visit(if_symboltable)
        if self.check_type(result.token.type, [TokenTypes.TUPLE_TYPE, TokenTypes.CHOICE]):
            return result.nodes[0]
        return result 
    
    def getChildNodes(self):
        childNodes = []

        childNodes.extend(self.if_node.getChildNodes()) 
        childNodes.extend(self.then_node.getChildNodes())
        childNodes.extend(self.else_node.getChildNodes())
        return childNodes
        
    # checks if a type exists in the following type list.
    def check_type(self,type:TokenTypes,types:list[TokenTypes]) -> bool:
        return type in types

    def App_Beta(self,identifierFrom, identifierTo):
        self.if_node.App_Beta(identifierFrom, identifierTo)
        self.then_node.App_Beta(identifierFrom, identifierTo)
        self.else_node.App_Beta(identifierFrom, identifierTo)

'''
Node for rigid equals.
''' 
class RigidEqNode(BaseNode):
    def __init__(self, token:Token, left_node:BaseNode, right_node:BaseNode) -> None:
        super().__init__(token)
        self.left_node = left_node
        self.right_node = right_node

    def __repr__(self) -> str:
        return "{}{}{}".format(repr(self.left_node),self.token.value, repr(self.right_node)) 

    def visit(self, symboltable: SymbolTable):
        res_left = self.left_node.visit(symboltable)
        res_right = self.right_node.visit(symboltable) # x = r:int
        if res_left.token.type != TokenTypes.IDENTIFIER and res_right.token.type != TokenTypes.IDENTIFIER:
            if res_left.token.value == res_right.token.value:
                return res_left
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.left_node.getChildNodes()) 
        childNodes.extend(self.right_node.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.left_node.App_Beta(identifierFrom, identifierTo)
        self.right_node.App_Beta(identifierFrom, identifierTo)
       


'''
Node for flexible equals.
''' 
class FlexibleEqNode(BaseNode):
    def __init__(self, token:Token, left_node:BaseNode, right_node:BaseNode) -> None:
        super().__init__(token)
        self.left_node = left_node
        self.right_node = right_node
        self.alreadyExists = False

    def visit(self, symboltable: SymbolTable):
        isValid = symboltable.addValue(self.left_node.token.value, self.right_node)
        if isValid:
            return self.right_node.visit(symboltable)
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))

    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.left_node.getChildNodes()) 
        childNodes.extend(self.right_node.getChildNodes())
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        self.left_node.App_Beta(identifierFrom, identifierTo)
        self.right_node.App_Beta(identifierFrom, identifierTo)

'''
Node for sequences (tuple, array).
''' 

class SequenceNode(BaseNode):
    def __init__(self, token:Token, nodes:list[BaseNode]) -> None:
        super().__init__(token)
        self.nodes = nodes
        self.seperator = ","
        
    def __repr__(self) -> str:    
        return "(" + self.seperator.join([repr(n) for n in self.nodes]) + ")"

    def visit(self, symboltable: SymbolTable):
        visited_nodes = []
        isChoice = False
        for n in self.nodes:
            visited_node = n.visit(symboltable).visit(symboltable)
            if visited_node.token.type == TokenTypes.FAIL:
                return FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value))
            elif visited_node.token.type == TokenTypes.CHOICE:
                isChoice = True
            visited_nodes.append(visited_node)
        
        sequentor:Sequentor = Sequentor(visited_nodes)
        sequences = sequentor.getSequences()

        if len(sequences) == 0:
            return FailNode(TokenTypes.FAIL,TokenTypes.FAIL.value)
        
        if len(sequences) == 1:
            if isChoice:
                return ChoiceSequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),sequences[0])
            return SequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),sequences[0])

        seq_nodes = []

        for s in sequences:
            seq_nodes.append(SequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),s))

        if isChoice:
            return ChoiceSequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),seq_nodes) 
        return SequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),seq_nodes) 

    def getChildNodes(self):
        childNodes = []
        for n in self.nodes:
            childNodes.extend(n.getChildNodes()) 
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        for n in self.nodes:
            n.App_Beta(identifierFrom, identifierTo)


'''
Node for indexing.
''' 
class IndexingNode(BaseNode):
    def __init__(self, token:Token,identifier:IdentifierNode, index:BaseNode) -> None:
        super().__init__(token)
        self.identifier = identifier
        self.index = index

    def visit(self, symboltable: SymbolTable):
        (isValid, result) = symboltable.get_value(self.identifier.token.value)
        if isValid and result != None:
            value = result.visit(symboltable)
            index = self.index.visit(symboltable)
            try:
                # checks if it is number
                if index.value >= len(value.nodes):
                    print("Exception -> Index out of range")
                    return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))

                return value.nodes[index.value]
            except:
                # checks if it is tuple
                try:
                    result = []
                    for iNode in index.nodes:
                        i = iNode.visit(symboltable)
                        if i.value >= len(value.nodes):
                            print("Exception -> Index out of range")
                            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
                        result.append(value.nodes[i.value])
                    return SequenceNode(Token(TokenTypes.TUPLE_TYPE,TokenTypes.TUPLE_TYPE.value),result)
                except:
                    return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
                    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.index.getChildNodes()) 
        return childNodes
    


'''
Node for choices sequences(branches of a listing of choices).
''' 
class ChoiceSequenceNode(BaseNode):
    def __init__(self, token:Token, nodes:list[BaseNode]) -> None:
        super().__init__(token)
        self.nodes = nodes
        self.seperator = "|"
        
        # Current choice branch/nodes index.
        self.currentChoice:int = 0 

        # Current val index for current choice branch/nodes.
        self.currentVal:int = - 1 

        # Gets the vals of current choice branch.
        self.getVals = self.getValsOfChoice() #--> Need to do something different
        
    def __repr__(self) -> str:    
        return "(" + self.seperator.join([repr(n) for n in self.nodes]) + ")"

    def visit(self, symboltable: SymbolTable):
        nodes = []

        # Choice appends all of its sequence, not containing false?
        if self.token.type == TokenTypes.CHOICE:
            for n in self.nodes:
                    # clonedTable = symboltable.createChildTable()
                    # current_n = n.visit(clonedTable).visit(clonedTable)
                    current_n = n.visit(symboltable).visit(symboltable)

                    # Skip fail node
                    if current_n.token.type != TokenTypes.FAIL:
                         nodes.append(current_n)  

            # If choise sequence is empty, return false?
            if(len(nodes) == 0):
                return FailNode(Token(TokenTypes.FAIL,TokenTypes.FAIL.value))
            
            # If choise has atleast one return the node it only contains instead od a choice sequence node.
            if(len(nodes) == 1):
                  # HIER GEÄNDERT  anstatt nodes[0].node nur nodes[0], weil es nur ein node ist und kein visitornode
                 return nodes[0]
            
            # At last, return choice sequence node wit all visited values.
            return ChoiceSequenceNode(self.token, nodes) 
    

    '''
    Gets the vals of the current choice branch.
    ''' 
    def getValsOfChoice(self):
        val = []
        current_node = self.nodes[self.currentChoice]
        if self.currentChoice > len(self.nodes) - 1:
            return None
        try:
            if current_node.token.type == TokenTypes.CHOICE:
                for v in current_node.yieldVal():
                    val.append(v)
                return val
        except:
            return [current_node]
        else: return [current_node]

    '''
    Steps to the next choice if possible.
    
    If:
    no choice branches available (Index of choice is at the last choice branch),
    set choice branch index back to the beginning choice branch, choice branch at index 0
    and set back the index counter for the values of the choice branch at current index.
    Return False indicating, no choice branches left.
    Else:
    
    Step to the next choice branch.
    Set counter back, so it can start at the beginning of the current choice branch, as
    soon get next val method is called.
    Return True indicating next choice branch has been selected.
    ''' 
    def nextChoice(self) -> bool:
           
        if self.currentChoice + 1 > len(self.nodes) - 1:
            self.setChoiceBack()
            self.setValCountBack()
            return False       
        else: 
            self.currentChoice += 1
            self.setValCountBack()
            self.getVals = self.getValsOfChoice()         
            return True     


    '''
    Set back the current choice branch index to 0 and its value index also to its starting integer value.
    '''
    def setChoiceBack(self):
        self.currentChoice = 0
        self.setValCountBack()
        self.getVals = self.getValsOfChoice()


    '''
    Sets the val to -1, so when get next val is called, its steps forward to index 0. 
    '''
    def setValCountBack(self):
        self.currentVal = -1
    

    '''
    Gets the next val of current choice branch. Repeats the selection of a choice branch, if requested.
    Needs to repeat the values for a choice branch, except for the last choices node during operation.
    '''
    def getNextVal(self, repeat:bool):
        if self.currentVal + 1 > len(self.getVals) - 1 and repeat: # If first val none, maybe error
            self.setValCountBack()
            self.currentVal += 1
            return self.getVals[self.currentVal]
        else:
            self.currentVal += 1
            return self.getVals[self.currentVal]
        
    '''
    Checks if current choice branch has a next value.
    Return wheter if its True or not.
    '''
    def hasNextVal(self):
        nextValExists = self.currentVal < len(self.getVals) - 1
        return nextValExists


    '''
    Yields all values of a choice branch.
    '''
    def yieldVal(self):
        for c in self.nodes:   
            if c.token.type == TokenTypes.CHOICE:
                yield c.yieldVal()
            else: yield c

    def getChildNodes(self):
        childNodes = []
        for n in self.nodes:
            childNodes.extend(n.getChildNodes()) 
        return childNodes
    
    def App_Beta(self,identifierFrom, identifierTo):
        for n in self.nodes:
            n.App_Beta(identifierFrom, identifierTo)
       

class DotDotNode(BaseNode):
    def __init__(self, token:Token, start:BaseNode, end:BaseNode) -> None:
        super().__init__(token)
        self.start = start
        self.end = end

    def visit(self, symboltable: SymbolTable):
        startNode = self.start.visit(symboltable)
        if startNode.token.type != TokenTypes.INTEGER:
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        
        endNode = self.end.visit(symboltable)
        if endNode.token.type != TokenTypes.INTEGER:
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        
        fac = 1
        if startNode.value > endNode.value:
            fac = -1

        nodes = []
        nodes.append(startNode)

        currentInt = startNode.value
        endGen = False

        while endGen == False:
            if currentInt == endNode.value:
                endGen = True
            else:
                currentInt += fac
                nodes.append(NumberNode(Token(TokenTypes.INTEGER,currentInt)))
           
        return ChoiceSequenceNode(Token(TokenTypes.CHOICE,TokenTypes.CHOICE.value), nodes)
    
    def getChildNodes(self):
        childNodes = []
        childNodes.extend(self.start.getChildNodes()) 
        childNodes.extend(self.end.getChildNodes()) 
        return childNodes

'''
Fail node indicating false? in Verse.
'''
class FailNode(BaseNode): # Technically not need, since Fail node is 1 to 1 a BaseNode
    def __init__(self, token:Token) -> None:
        super().__init__(token)
    
    def __repr__(self) -> str:    
        return self.token.value 

    def visit(self, symboltable: SymbolTable):
        return self 
    
    def getChildNodes(self):
        childNodes = [self]
        return childNodes
    
   

class LambdaNode(BaseNode):
    def __init__(self, token:Token, params:list[ScopeNode], body:BlockNode, values:list[BaseNode]) -> None:
        super().__init__(token)
        self.params = params
        self.body = body
        self.values = values
    
    def __repr__(self) -> str:    
        return "( " +  ",".join([repr(param) for param in self.params]) + " " + self.token.value + " " + repr(self.body) + " )" + "".join([" (" + repr(n) + ")" for n in self.values])

    def visit(self, symboltable: SymbolTable):
        if(len(self.params) != len(self.values)):
            return FailNode(Token(TokenTypes.FAIL, TokenTypes.FAIL.value))
        copiedTable = symboltable.createChildTable()
        self.Rename(copiedTable)
        copybody = copy.deepcopy(self.body)
        newbody = BlockNode([])

        index = 0
        for p in self.params:
            pav = FlexibleEqNode(Token(TokenTypes.EQUAL, TokenTypes.EQUAL.value),p.nodes[0],self.values[index].visit(symboltable))
            index +=1
            newbody.nodes.append(pav)
        newbody.nodes.append(copybody)
        result = newbody.visit(copiedTable)
        return result 
    
        
    def getChildNodes(self):
        childNodes = [self]
        return childNodes

    
    def getChildNodes(self):
        childNodes = [self]
        return childNodes
    
    def Rename(self, symboltable:SymbolTable):
        symbols = []
        for s in symboltable.symboltable:
            symbols.append(s.symbol)

        
        for param in self.params:
            if symboltable.check_if_exists(param.nodes[0].token.value):
                newIdentifier = IdentifierCreator.create(symboltable)
                self.body.App_Beta(param.nodes[0].token.value, newIdentifier)
                param.nodes[0].token.value = newIdentifier
            param.visit(symboltable)
    
    def App_Beta(self, identifierFrom, identifierTo):
        for v in self.values:
            v.App_Beta(identifierFrom, identifierTo)
        
        for param in self.params:
            param.App_Beta(identifierFrom, identifierTo)
        self.body.App_Beta(identifierFrom, identifierTo)