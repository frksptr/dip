class StateMachine:
   currentState =""
   stateMap = {}
   printEn = 0
   def __init__(self, states):
       self.stateMap = states
       self.currentState = self.stateMap[0].prevState
       
   def event(self, event):
       x = next((x for x in self.stateMap if x.event == event), None)
       if (x == None):
          if(self.printEn == 1):
             print("invalid action {}".format(event))
          return
       if (x.prevState != self.currentState):
          if(self.printEn == 1):
             print("invalid transition")
          return
       print("{}: {} -> {}".format(x.event,x.prevState,x.nextState))
       self.currentState = x.nextState
       
        

class StateMapElement:
    event=""
    prevState=""
    nextState=""
    def __init__(self, event, prevState, nextState):
        self.event = event
        self.prevState = prevState
        self.nextState = nextState
