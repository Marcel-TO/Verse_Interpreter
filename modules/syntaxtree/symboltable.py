import string
from structure.tokenTypes import TokenTypes
from structure.logger import Console_Logger

class Symbol:
    def __init__(self, symbol: string, value, symbolType: TokenTypes, insideTable) -> None:
        self.symbol: string = symbol
        self.value = value
        self.symbolType: TokenTypes | None = symbolType
        self.insideTable = insideTable

class SymbolTable:
    def __init__(self) -> None:
        self.symboltable: list[Symbol] = []
        self.logger = Console_Logger()
    
    def __info__(self) -> None:
        for symbol in self.symboltable:
            self.logger.__log__("Symboltable: Name= {}, Value= {}, type= {} and inside table={}".format(symbol.symbol, symbol.value, symbol.symbolType, symbol.insideTable))
    
    def check_if_exists(self, symbol: string, table) -> bool:
        for sym in self.symboltable:
            if sym.symbol == sym and table == sym.insideTable:
                return True
        return False
    
    def addScope(self, symbol: string, symbolType: TokenTypes) -> None:
        # checks if the name already exists in the current symbol. Otherwise add to table.
        if self.check_if_exists(symbol, self) == False:
            self.symboltable.append(Symbol(symbol, None, symbolType, self))
            self.logger.__log__("Added the Symbol: {} to the symboltable: {}".format(symbol, self))
    
    def addValue(self, symbol: string, value) -> None:
        # checks if the symbol is already defined with type or value.
        for sym in self.symboltable:
            if sym.symbol == symbol and sym.symbolType != None and sym.value == None and value != None:
                sym.value = value
                self.logger.__log__("Added the value: {} to the existing symbol: {} in the symboltable: {}".format(value, sym.symbol, self))
    
    def addBinding(self, symbol: string, value, symbolType: TokenTypes) -> None:
        # checks if the name already exists in the current symbol. Otherwise add to table.
        if self.check_if_exists(symbol, self) == False:
            self.symboltable.append(Symbol(symbol, value, symbolType, self))
            self.logger.__log__("Added the Symbol: {} to the symboltable: {}".format(symbol, self))
    
    def addSymbolTable(self, symboltable) -> None:
            # checks if the name already exists in the current symbol. Otherwise add to table.
            for sym in symboltable.symboltable:
                if self.check_if_exists(sym.symbol, symboltable) == False:
                    self.symboltable.append(Symbol(sym.symbol, sym.value, sym.symbolType, symboltable))
                    self.logger.__log__("Added the Symbol: {} from the symboltable: {}".format(sym.symbol, symboltable))

    
    def remove(self, symbol:string, value, symbolType: type) -> None:
        # checks if the table is empty.
        if len(self.symboltable) < 1:
            return
        
        # iterates through and removes the corresponding 
        for sym in self.symboltable:
            if sym.symbol == symbol:
                if sym.insideTable == self:
                    self.symboltable.remove(Symbol(sym.symbol, sym.value, sym.symbolType, self)) 
                    self.logger.__log__("Removed the Symbol: {} to the scopetable".format(symbol))
    
    def get_value(self, symbol: string, symboltable) -> tuple[bool]:
        for sym in self.symboltable:
            if sym.symbol == symbol:
                if sym.insideTable == symboltable:
                    return True, sym.value
        return False, None