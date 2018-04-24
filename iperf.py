#!/usr/bin/env python
'''
GUI for Iperf3
N Waterton V 1.0 19th April 2018: initial release
'''

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__VERSION__ = '1.0'

import subprocess, sys, os, tempfile
from platform import system as system_name  # Returns the system/OS name
import time
import Tkinter as tk
import ttk
import meter as m
HAVE_PING = False
try:
    import pyping
    HAVE_PING = True
except ImportError:
    pass

class Mainframe(tk.Frame):
    
    def __init__(self,master, arg=None, *args,**kwargs):
        #super(Mainframe,self).__init__(master,*args,**kwargs)
        tk.Frame.__init__(self, master, *args,**kwargs)
        self.arg = arg
        self.master = master
        self.server_list = [self.arg.ip_address,
                            'iperf.he.net',
                            'bouygues.iperf.fr',
                            'ping.online.net',
                            'ping-90ms.online.net',
                            'iperf.eenet.ee',
                            'iperf.volia.net',
                            'iperf.it-north.net',
                            'iperf.biznetnetworks.com',
                            'iperf.scottlinux.com']
        self.port_list   = ['5200',
                            '5201',
                            '5202',
                            '5203',
                            '5204',
                            '5205',
                            '5206',
                            '5207',
                            '5208',
                            '5209']
        self.max_options = ['OFF', 'Track Needle', 'Hold Peak']
        self.max_range = 1000
        self.min_range = 10
        self.resolution = 10
        #self.ranges = list(range(self.min_range, self.max_range+self.resolution, self.resolution))
        self.ranges = [10,30,50,100,200,400,600,800,1000]
        self.duration = tk.Variable()
        self.threads = tk.Variable()
        self.server = tk.Variable()
        self.server_port = tk.Variable()
        self.range = tk.Variable()
        self.reset_range = tk.Variable()
        self.threads.set('16')
        self.reset_range.set(self.arg.reset_range)
        
        self.msg_label = tk.Label(self, text="Ping:")
        self.msg_label.grid(row=0, sticky=tk.E)
        self.ping_label = tk.Label(self, anchor='w', width=60)
        self.ping_label.grid(row=0, column=1, columnspan=3, sticky=tk.W)
        
        tk.Label(self, text="Download:").grid(row=2, sticky=tk.E)
        self.download_label = tk.Label(self, anchor='w', width=60)
        self.download_label.grid(row=2, column=1, columnspan=3, sticky=tk.W)
        
        tk.Label(self, text="Upload:").grid(row=3, sticky=tk.E)
        self.upload_label = tk.Label(self, anchor='w', width=60)
        self.upload_label.grid(row=3, column=1, columnspan=3, sticky=tk.W)
 
        self.meter = m.Meter(self,height = 300,width = 300)
        self.range.trace('w',self.updaterange)  #update range when value changes
        self.range.set(self.arg.range)
        self.meter.set(0)
        self.meter.grid(row=4, column=0, columnspan=4)
 
        tk.Label(self, text="Server:").grid(row=5, sticky=tk.E)
        self.ipaddress= ttk.Combobox(self, textvariable=self.server, values=self.server_list, width=39)
        self.ipaddress.current(0)
        self.ipaddress.grid(row=5, column=1, columnspan=2, sticky=tk.W)
        
        self.port= ttk.Combobox(self, textvariable=self.server_port, values=self.port_list, width=4)
        if self.arg.port in self.port_list:
            self.port.current(self.port_list.index(self.arg.port))
        else:
            self.port_list.insert(0,self.arg.port)
            self.port.config(values=self.port_list, width=len(self.arg.port))
            self.port.current(0)
        self.port.grid(row=5, column=3, sticky=tk.W)
        
        tk.Label(self, text="Progress:").grid(row=6, sticky=tk.E)
        self.progress_bar = ttk.Progressbar(self
        ,orient="horizontal"
        ,length=325
        , mode="determinate")
        self.progress_bar.grid(row=6, column=1, columnspan=3, sticky=tk.W)
        
        tk.Label(self, text="Peak Mode:").grid(row=7, sticky=tk.E)
        self.max_mode_value = tk.StringVar()
        try:
            self.max_mode_value.set(self.max_options[arg.max_mode_index])
        except ValueError:
            self.max_mode_value.set(self.max_options[0]) # default value
        self.max_mode = tk.OptionMenu(self
         ,self.max_mode_value
         ,*self.max_options)
        self.max_mode.grid(row=7, column=1, columnspan=2, sticky=tk.W)
 
        #tk.Scale(self,width = 15 ,from_ = self.min_range, to = self.max_range
        #,resolution = self.resolution
        #,orient = tk.HORIZONTAL
        #,label='Set Range'
        #,variable=self.range
        #,command = self.setrange).grid(row=8, column=0, rowspan=2)
        
        tk.Checkbutton(self, text="Reset Range for Upload", variable=self.reset_range).grid(row=7, column=2, columnspan=2, sticky=tk.W)
        
        tk.Label(self, text="Range:").grid(row=8, sticky=tk.W)
        ttk.Combobox(self, textvariable=self.range, values=self.ranges, width=4).grid(row=9, column=0, rowspan=2)
        
        tk.Scale(self,width = 15 ,from_ = 10, to = 30
        ,orient = tk.HORIZONTAL
        ,label='Test Duration'
        ,variable=self.duration).grid(row=8, column=1, rowspan=2)
        
        tk.Scale(self,width = 15 ,from_ = 1, to = 30
        ,orient = tk.HORIZONTAL
        ,label='Threads'
        ,variable=self.threads).grid(row=8, column=2, rowspan=2)
        '''
        tk.Scale(self,width = 15 ,from_ = 0, to = self.max_range
        ,orient = tk.HORIZONTAL
        ,label='Debug'
        ,command = self.setmeter).grid(row=8, column=0)
        '''
        tk.Button(self,text = 'Start',width = 15,command = self.run_iperf).grid(row=8, column=3)
        self.quit = tk.Button(self,text = 'Quit',width = 15,command = self.quit)
        self.quit.grid(row=9, column=3)

    def ping(self,host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """
        success = True
        ping_rtt = ''
        # Ping command count option as function of OS
        param = '-n 1' if system_name().lower()=='windows' else '-c 1'

        # Building the command. Ex: "ping -c 1 google.com"
        command = 'ping %s %s' % (param, host)
        
        self.print('Ping command: %s' % command)

        # Pinging
        p = subprocess.Popen(command.split(), stdout = subprocess.PIPE)
        while True:
            result = p.stdout.readline()
            self.print('ping: %s' % result)
            if result == '':
                break
            else:
                if 'avg' in result.lower() or 'average' in result.lower():
                    ping_rtt = result.replace('imum','').strip()
                if 'unreachable' in result.lower():
                    success = False
                    
        p.terminate()
        return success, ping_rtt
        
    def quit(self):
        print("Exit Program")
        self.done = True
        try:
            self.p.terminate()
            time.sleep(1)
        except AttributeError:
            pass
        
        self.master.destroy()
        sys.exit(0)
        
    def run_iperf(self):
        ping_ok = True
        self.msg_label.config(text='Ping:')
        self.ping_label.config(text='Testing')
        self.download_label.config(text='', width=60)
        self.upload_label.config(text='', width=60)
        self.meter.draw_bezel() #reset bezel to default
        self.update_idletasks()
        if HAVE_PING:
            result = pyping.ping(self.server.get())                # Need to be root or Administrator in Windows
            if result.ret_code != 0:
                self.msg_label.config(text='Error:')
                message = 'Could not ping server %s(%s)' % (self.server.get(),result.destination_ip)
                ping_ok = False
            else:
                message = 'Min = %sms, Max = %sms, Average = %sms' % (result.min_rtt, result.max_rtt, result.avg_rtt)
            self.print('Ping: %s' % message)
        else:
            result, rtt = self.ping(self.server.get())
            if not result:
                self.msg_label.config(text='Error:')
                message = 'Could not ping server %s' % self.server.get()
                ping_ok = False
            else:
                message = '%s' % rtt
        self.ping_label.config(text=message)
        self.update_idletasks()
        if ping_ok:
            if len(self.run_iperf3(upload=False)) != 0 and not self.done: #if we get some results (not an error)
                if int(self.reset_range.get()) == 1:
                    self.range.set(self.arg.range)  #reset range to default
                self.run_iperf3(upload=True)
        
        
    def run_iperf3(self, upload=False):
        self.done = False
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = int(self.duration.get())
        self.meter.max_val = 0
        self.meter.set(0)
        self.meter.show_max = self.max_options.index(self.max_mode_value.get()) #get index of item selected in max options
        fname = tempfile.NamedTemporaryFile()
        if system_name().lower()=='windows':
            iperf_command = '%s -c %s -p %s -P %s -O 1 -t %s %s --logfile %s' % (self.arg.iperf_exec,
                                                                                self.server.get(), 
                                                                                self.server_port.get(),
                                                                                self.threads.get(),
                                                                                self.duration.get(),
                                                                                '' if upload else '-R',
                                                                                fname.name)
        else:
            iperf_command = '%s -c %s -p %s -P %s -O 1 -t %s %s '         % (self.arg.iperf_exec,
                                                                                self.server.get(), 
                                                                                self.server_port.get(),
                                                                                self.threads.get(),
                                                                                self.duration.get(),
                                                                                '' if upload else '-R')
        
        self.print("command: %s" % iperf_command)
        if upload:
            self.upload_label.config(text='Testing')
        else:
            self.download_label.config(text='Testing')   

        try:
            self.p = subprocess.Popen(iperf_command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            self.msg_label.config(text='%s:' % sys.exc_info()[0].__name__)
            self.ping_label.config(text='(%s) %s' % (self.arg.iperf_exec,e))
            print('Error in command: %s\r\n%s' % (iperf_command,e))
            return []
        
        with fname:
            results_list = self.progress(fname if system_name().lower()=='windows' else self.p.stdout, upload)
            
        try:
            self.p.terminate()
            self.setmeter(0)
            self.update_idletasks()
        except (tk.TclError, AttributeError):
            pass
        self.print('End of Test')
        return results_list
        
    def progress(self,capture, upload):
        results_list = []
        while not self.done:
            try:
                line = capture.readline()
                if self.arg.verbose and line: self.print(line.strip())
                if 'Done' in line:
                    break
                if 'Connecting' in line:
                    continue
                if 'error' in line:
                    self.print("%s" % line)
                    self.msg_label.config(text='Error:')
                    self.ping_label.config(text=line.strip())
                    self.upload_label.config(text='')
                    self.download_label.config(text='')
                    break
                else:
                    if (int(self.threads.get()) > 1 and line.startswith('[SUM]')) or (int(self.threads.get()) == 1 and 'bits/sec' in line):
                        self.progress_bar["value"] += 1
                        speed = float(line.decode('utf-8').replace('[ ','[').replace('[ ','[').split()[5])
                        units = line.decode('utf-8').replace('[ ','[').replace('[ ','[').split()[6]
                        if 'receiver' in line:
                            total = speed
                            self.print("Total: %s %s" % (total, units))
                            if upload:
                                self.upload_label.config(text='Max = %s, Avg = %s %s' % (max(results_list), total, units))
                            else:
                                self.download_label.config(text='Max = %s, Avg = %s %s' % (max(results_list), total, units))
                            results_list.append(total)
                        else:
                            self.print("Speed: %s %s" % (speed, units))
                            #update range if value is too high
                            if speed > self.meter.range+(self.meter.range/20):  #if more than 5% over-range
                                self.setrange(next((i for  i in self.ranges if i>=speed),self.ranges[-1]))  #increase range if possible
                            self.setmeter(speed)
                            self.setunits(units)
                            self.quit.update()
                            self.update_idletasks()
                        results_list.append(speed)
            except tk.TclError:
                break
        capture.close()
        return results_list
        
    def print(self, str):
        if self.arg.debug:
            print(str)
            
    def updaterange(self, *args):
        self.setrange(self.range.get())
        
    def setrange(self, value):
        self.range.set(value)
        try:
            self.meter.setrange(0,int(value))
        except ValueError:
            self.meter.setrange(0,self.ranges[0])
        
    def setunits(self,value):
        self.meter.units(value)
        
    def setmeter(self,value):
        value = int(value)
        #self.meter.set(value, True)
        self.meter.smooth_set(value, True)
        
class App(tk.Tk):
    def __init__(self, arg):
        #super(App,self).__init__()
        tk.Tk.__init__(self)
        self.title('Iperf3 Network Speed Meter')
        Mainframe(self, arg=arg).grid()


def main():
    import argparse
    max_mode_choices = ['OFF', 'Track', 'Peak']
    parser = argparse.ArgumentParser(description='Iperf3 GUI Network Speed Tester')
    parser.add_argument('-I','--iperf_exec', action="store", default='iperf3', help='location and name of iperf3 executable (default=%(default)s)')
    parser.add_argument('-ip','--ip_address', action="store", default='192.168.100.119', help='default server address (default=%(default)s)')
    parser.add_argument('-p','--port', action="store", default='5201', help='server port (default=%(default)s)')
    parser.add_argument('-r','--range', action="store", type=int, default=10, help='range to start with in Mbps (default=%(default)s)')
    parser.add_argument('-R','--reset_range', action='store_false', help='Do NOT Reset range to Default for Upload test', default = True)
    parser.add_argument('-m','--max_mode', action='store', choices=max_mode_choices, help='Show Peak Mode (default = %(default)s)', default = max_mode_choices[2])
    parser.add_argument('-D','--debug', action='store_true', help='debug mode', default = False)
    parser.add_argument('-V','--verbose', action='store_true', help='print everything', default = False)
    parser.add_argument('-v','--version', action='version',version='%(prog)s {version}'.format(version=__VERSION__))

    arg = parser.parse_args()
    if arg.verbose: arg.debug=True
    arg.max_mode_index = max_mode_choices.index(arg.max_mode)
    
    App(arg).mainloop()

    
if __name__ == "__main__":
    main()