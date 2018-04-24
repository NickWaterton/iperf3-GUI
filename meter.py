import Tkinter as tk
import tkFont as tkf
import math, time

# class to show a gauge or panel meter
class Meter(tk.Canvas):
    def __init__(self,master,*args,**kwargs):
        #super(Meter,self).__init__(master,*args,**kwargs)
        tk.Canvas.__init__(self, master,*args,**kwargs)
        self.ranges = [100] #default range
        self.tick_values =[]
        self.show_max = 0
        self.max_val = 0
        self.range = self.ranges[0]
        self.current_value = 0
        self.smooth_step_slow = 5
        self.smooth_step_fast = 10
        self.smooth_step = self.smooth_step_slow    #default
        self.layoutparams()
        self.graphics()
        self.createhand()
        self.setrange()
        
    def layoutparams(self):
        # set parameters that control the layout
        height = int(self['height'])
        width = int(self['width'])
        
        # find a square that fits in the window
        if(height*2 > width):
            side = width
        else:
            side = height*2
        
        # set axis for hand
        self.centrex = side/2
        self.centrey = side/2
        
        # standard with of lines
        self.linewidth = 2
        
        # outer radius for dial
        self.radius = int(0.40*float(side))
        
        # set width of bezel
        self.bezel = self.radius/15
        self.bezelcolour1 = '#c0c0c0'
        self.bezelcolour2 = '#808080'
    
        # set lengths of ticks and hand
        self.majortick = self.radius/8
        self.minortick = self.majortick/2
        self.handlen = self.radius - self.majortick - self.bezel - 1
        self.blobrad = self.handlen/6
             
    def graphics(self):
        # create the static components
        self.draw_bezel()
        
        for deg in range(-60,241,6):
            self.createtick(deg,self.minortick)
        for deg in range(-60,241,30):
            self.createtick(deg,self.majortick)
            
    def draw_bezel(self):
        self.create_oval(self.centrex-self.radius
        ,self.centrey-self.radius
        ,self.centrex+self.radius
        ,self.centrey+self.radius
        ,width = self.bezel
        ,outline = self.bezelcolour2)
    
        self.create_oval(self.centrex-self.radius - self.bezel
        ,self.centrey-self.radius - self.bezel
        ,self.centrex+self.radius + self.bezel
        ,self.centrey+self.radius + self.bezel
        ,width = self.bezel
        ,outline = self.bezelcolour1)
        
        for angle in [60, 0, 300]:
            self.create_arc(self.centrex-self.radius
            ,self.centrey-self.radius
            ,self.centrex+self.radius
            ,self.centrey+self.radius
            ,width = self.bezel
            ,style = tk.ARC
            ,start = angle
            ,extent = 180 if angle == 60 else 60
            ,outline = 'green' if angle==60 else 'orange' if angle==0 else 'red')
        
    def createhand(self):
        # create text value display
        self.textid = self.create_text(self.centrex
        ,self.centrey - 3*self.blobrad
        ,fill = 'red'
        ,font = tkf.Font(size = -int(2*self.majortick)))
        
        # create units display
        self.unitsid = self.create_text(self.centrex
        ,self.centrey + 3*self.blobrad
        ,fill = 'black'
        ,font = tkf.Font(size = -int(2*self.majortick)))
        
        # create moving and changeable bits
        self.handid = self.create_line(self.centrex,self.centrey
        ,self.centrex - self.handlen,self.centrey
        ,width = 2*self.linewidth
        ,fill = 'red')
        
        self.blobid = self.create_oval(self.centrex - self.blobrad
        ,self.centrey - self.blobrad
        ,self.centrex + self.blobrad
        ,self.centrey + self.blobrad
        ,outline = 'black', fill = 'black')
        
    def createtick(self,angle,length):
        # helper function to create one tick
        rad = math.radians(angle)
        cos = math.cos(rad)
        sin = math.sin(rad)
        radius = self.radius - self.bezel
        if length == self.majortick:    #label major ticks
            value = str(int(float(angle+60)/300.0*self.range))
            self.tick_values.append(self.create_text(self.centrex - (radius - length - 10)*cos, self.centrey - (radius - length - 10)*sin, text=value))
        self.create_line(self.centrex - radius*cos
        ,self.centrey - radius*sin
        ,self.centrex - (radius - length)*cos
        ,self.centrey - (radius - length)*sin
        ,width = self.linewidth
        ,fill = 'green' if angle< 120 else 'orange' if angle < 180 else 'red')
        
    def setrange(self,start = 0, end=100):
        self.start = start
        self.range = end - start
        self.current_value = start
        for val_index, angle in enumerate(range(-60,241,30)):   #relabel major ticks.
            value = str(int(float(angle+60)/300.0*self.range))
            self.itemconfigure(self.tick_values[val_index],text = value)
        
    def units(self,text):
        self.itemconfigure(self.unitsid,text = str(text))
        
    def smooth_set(self, value, arc=False):
        #do a smooth update, rather than jump to value
        tmp_value = self.current_value

        while self.current_value < value or self.current_value > value:
            step = min(self.smooth_step, max(1,abs(value-self.current_value)))
            if value < self.current_value:
                step = -step
            tmp_value = max(0,tmp_value+step)
            self.set(tmp_value, arc)
            #time.sleep(0.01)
            time_delay = 1.0/(max(1.0,float(abs(value-self.current_value)))*0.5)
            #print("step: %s delay: %s, tmp_value: %s value: %s current_value: %s" % (step, time_delay,tmp_value, value, self.current_value))
            time.sleep(min(0.1,time_delay))
            self.update_idletasks()

        self.set(value, arc)
        
    def set(self,value, arc=False):
        # call this to set the hand (jump to value)
        self.current_value = value
        #update range if value is too high
        if value > self.range+(self.range/20):  #if more than 5% over-range
            self.setrange(end=next((i for  i in self.ranges if i>=value),self.ranges[-1]))  #increase range if possible

        # convert value to range 0,100
        deg = 300*(value - self.start)/self.range - 240
        
        self.itemconfigure(self.textid,text = str(value))
        self.itemconfigure(self.textid,fill = 'green' if int(value) < self.range*6/10 else 'orange' if int(value) < self.range*8/10 else 'red')
            
        rad = math.radians(deg)
        # reposition hand
        self.coords(self.handid,self.centrex,self.centrey
        ,self.centrex+self.handlen*math.cos(rad), self.centrey+self.handlen*math.sin(rad))
        
        #draw arc if selected
        if arc:
            if self.show_max == 0:      #off
                self.smooth_step = self.smooth_step_slow
                return
            elif self.show_max == 1:    #live
                self.smooth_step = self.smooth_step_fast
            elif self.show_max == 2:    #hold peak
                self.smooth_step = self.smooth_step_fast
                if value < self.max_val:
                    return
                else:
                    self.max_val = value
            
            self.create_oval(self.centrex-self.radius - self.bezel
            ,self.centrey-self.radius - self.bezel
            ,self.centrex+self.radius + self.bezel
            ,self.centrey+self.radius + self.bezel
            ,width = self.bezel
            ,outline = self.bezelcolour1)
        
            self.create_arc(self.centrex-self.radius - self.bezel
            ,self.centrey-self.radius - self.bezel
            ,self.centrex+self.radius + self.bezel
            ,self.centrey+self.radius + self.bezel
            ,width = self.bezel
            ,style = tk.ARC
            ,start = max(360-deg, 300)
            ,extent = min(240+deg, 300)
            ,outline = 'blue')#'green' if angle==60 else 'orange' if angle==0 else 'red')
            '''
            self.create_arc(self.centrex-self.radius - self.bezel
            ,self.centrey-self.radius - self.bezel
            ,self.centrex+self.radius + self.bezel
            ,self.centrey+self.radius + self.bezel
            ,width = self.bezel
            ,style = tk.ARC
            ,start = 300
            ,extent = max(60-deg,0)
            ,outline = self.bezelcolour1)
            '''
            #print("value: %s, deg: %s" % (value,deg))
        
    def blob(self,colour):
        # call this to change the colour of the blob
        self.itemconfigure(self.blobid,fill = colour,outline = colour)