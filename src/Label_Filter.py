import logging as log

class Label_Filter(log.Filter):
    def __init__(self, label: str):
        super.__init__() #Llamar al constructor de la clase padre
        self.label = label
        
    
    def filter(self, record):
        return hasattr(record, 'label') and record.label == self.label
        