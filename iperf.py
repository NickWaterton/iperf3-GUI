#!/usr/bin/env python
'''
GUI for Iperf3
see https://iperf.fr/iperf-servers.php for details of list of servers given
N Waterton V 1.0 19th April 2018: initial release
N Waterton V 1.1 26th April 2018: Added geographic data
'''

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__VERSION__ = __version__ = '1.1'

import subprocess, sys, os, tempfile
from platform import system as system_name  # Returns the system/OS name
import time
import ConfigParser
import math
import json
import urllib2
import Tkinter as tk
import ttk
import meter as m
import re
import base64
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
        
        self.ip_address = None # ip address of current remote server
        self.arg = arg
        self.master = master
        self.ip_info = {}
        self.distance = 0
        self.local_ip = self.arg.local_ip
        if self.local_ip is None:
            self.local_ip = self.get_local_ip() #get local external ip if we can
        self.meter_size = 300 #meter is square
        self.no_response = 'No Response from iperf3 Server'
        self.server_list = ['iperf.he.net',
                            'bouygues.iperf.fr',
                            'ping.online.net',
                            'ping-90ms.online.net',
                            'iperf.eenet.ee',
                            'iperf.volia.net',
                            'iperf.it-north.net',
                            'iperf.biznetnetworks.com',
                            #speedtest.wtnet.de,
                            'iperf.scottlinux.com']
        self.server_list[0:0] = self.arg.ip_address
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
        #self.server.trace('w', self.servercalback)
        self.server_port = tk.Variable()
        self.range = tk.Variable()
        self.reset_range = tk.Variable()
        self.threads.set('16')
        self.reset_range.set(self.arg.reset_range) 

        self.read_config_file() #load data if config file exists
        self.get_ip_info(self.local_ip)
        #add any new servers in config file
        for k in self.ip_info.keys():
            new_server = self.ip_info[k].get('server', None)
            self.print('Checking server: %s' % new_server)
            if new_server not in self.server_list and new_server is not None and new_server != self.local_ip:
                self.print('Adding new server to list: %s' % new_server)
                self.server_list.append(new_server) 
        
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
        
        self.map = None
        self.map_panel = tk.Label(self)
        tk.Label(self, text="Destination:").grid(row=4, sticky=tk.E)
        self.geography_label = tk.Label(self, anchor='w', width=60)
        self.geography_label.grid(row=4, column=1, columnspan=3, sticky=tk.W)
        self.geography = tk.Variable()
        self.geography.set(self.arg.geography)
        self.geography.trace('w',self.updategeography)  #update range when value changes
        self.no_map = '''
            R0lGODlhGAEYAXAAACH5BAEAAPwALAAAAAAYARgBhwAAAAAAMwAAZgAAmQAAzAAA/wArAAArMwAr
            ZgArmQArzAAr/wBVAABVMwBVZgBVmQBVzABV/wCAAACAMwCAZgCAmQCAzACA/wCqAACqMwCqZgCq
            mQCqzACq/wDVAADVMwDVZgDVmQDVzADV/wD/AAD/MwD/ZgD/mQD/zAD//zMAADMAMzMAZjMAmTMA
            zDMA/zMrADMrMzMrZjMrmTMrzDMr/zNVADNVMzNVZjNVmTNVzDNV/zOAADOAMzOAZjOAmTOAzDOA
            /zOqADOqMzOqZjOqmTOqzDOq/zPVADPVMzPVZjPVmTPVzDPV/zP/ADP/MzP/ZjP/mTP/zDP//2YA
            AGYAM2YAZmYAmWYAzGYA/2YrAGYrM2YrZmYrmWYrzGYr/2ZVAGZVM2ZVZmZVmWZVzGZV/2aAAGaA
            M2aAZmaAmWaAzGaA/2aqAGaqM2aqZmaqmWaqzGaq/2bVAGbVM2bVZmbVmWbVzGbV/2b/AGb/M2b/
            Zmb/mWb/zGb//5kAAJkAM5kAZpkAmZkAzJkA/5krAJkrM5krZpkrmZkrzJkr/5lVAJlVM5lVZplV
            mZlVzJlV/5mAAJmAM5mAZpmAmZmAzJmA/5mqAJmqM5mqZpmqmZmqzJmq/5nVAJnVM5nVZpnVmZnV
            zJnV/5n/AJn/M5n/Zpn/mZn/zJn//8wAAMwAM8wAZswAmcwAzMwA/8wrAMwrM8wrZswrmcwrzMwr
            /8xVAMxVM8xVZsxVmcxVzMxV/8yAAMyAM8yAZsyAmcyAzMyA/8yqAMyqM8yqZsyqmcyqzMyq/8zV
            AMzVM8zVZszVmczVzMzV/8z/AMz/M8z/Zsz/mcz/zMz///8AAP8AM/8AZv8Amf8AzP8A//8rAP8r
            M/8rZv8rmf8rzP8r//9VAP9VM/9VZv9Vmf9VzP9V//+AAP+AM/+AZv+Amf+AzP+A//+qAP+qM/+q
            Zv+qmf+qzP+q///VAP/VM//VZv/Vmf/VzP/V////AP//M///Zv//mf//zP///wAAAAAAAAAAAAAA
            AAisAPcJHEiwoMGDCBMqXMiwocOHECNKnEixosWLGDNq3Mixo8ePIEOKHEmypMmTKFOqXMmypcuX
            MGPKnEmzps2bOHPq3Mmzp8+fQIMKHUq0qNGjSJMqXcq0qdOnUKNKnUq1qtWrWLNq3cq1q9evYMOK
            HUu2rNmzaNOqXcu2rdu3cOPKnUu3rt27ePPq3cu3r9+/gAMLHky4sOHDiBMrXsy4sePHkCNLnky5
            suXLmEgza97MubPnz6BDix5NurTp06hTq17NurXr17Bjy55Nu7bt27hz697Nu7fv38CDCx9OvLjx
            48iTK1/OvLnz59CjS59Ovbr169g4s2vfzr279+/gw4sfT768+fPo06tfz769+/fw48ufT7++/fv4
            8+vfz7+///8ABijggAQWaOCBCCb/aJs+iiQQzT60OKgQLRAcFOGDoLEDgAAY7qMPFUBAtAsAAYRS
            0IcAhJiRPoQAEAdFLEqoyAMLKVLBQTOKFgwAAFQo0IdGQLQOj0ESNCIARWLEjgBm+HiRLhImpIuT
            BEHZoWe7CHBJiQLlQ0UQIgoQCYcDsVjElxrRYsGSV1I0Y5sFKULlQG+Gto4ApjT4IJADzaMCjy4e
            FIwAz6jwokDsBAAKFUnSAqiTtBhxJJkGfRiHlyrSQimEEjrKI6SdRulpjwPRUoGGG2J4IaKARnlZ
            ltFo+CKmrB6qYZIDwaoFpBbQuo8iRfp5qCKkxggnm78+8KCsPzIKYbCGCpRjstJC/ztssYR0SuM+
            sHpIiLKYZXkKhBx+eISHchKkaZvlcJioifkYyueJ6e5jpUDycEkQgz6+622RS467b733rjqwj7SA
            u0++JiqCQDSWDuTvZXc+GK8RH4YYscT6DjToKV4GuYuDXoLpLaAAbEthn9ESJGyzRQbTqQU/tgjo
            tnpCCC6LKOPs5MsJR+MnyiSa+KoAAu+iqLMvS4x0Qd1qCo2zGaMrIb8CQbLtPk17THSqXK8QSsQM
            Xl1v0JxCnDPW9m4NNMktczYohh86AOI+XlI5rZFk+ikGmSFz3TKLCCucqMA1U8ksi0awI2HThEub
            gLQ0Qk5I4RgeTm3gnbWLOKrn7puzo62BFnTnuAyS6uHdHyKcskCOVph3QcyWSUW/CQDbrOsqg2tl
            67C//iups6fNrb6OwylZt6WWvg+qJCLON4YjHupl6EMDYIGa0lpwpKuwbxr+nlR0nP32NP8qo4Ty
            /Kk9988eqXCdot+sPHG6bK1gQvXuL6X+/gugAAdIwAIa8IAITKACF8jABjrwgRCMoAQnSMEKWvCC
            GMygBjM3yMEOevCDIAyhCEdIwhKa8IQoTKEKV8jCFrrwhTCMoQxnSMMa2vCGOMyhDnfIwx768Icu
            QAyiEIdIxCIa8YhITKISl8jEJjrxiVCMohSnSMUqWvGKWMyiFrfIxS568YtgDCGjGMdIxjKa8Yxo
            TKMa18jGNrrxjXCMoxznSMc62rE1AQEAOw==
            '''
 
        self.meter = m.Meter(self,height = self.meter_size,width = self.meter_size)
        self.range.trace('w',self.updaterange)  #update range when value changes
        self.range.set(self.arg.range)
        self.meter.set(0)
        self.meter.grid(row=5, column=0, columnspan=4)
 
        tk.Label(self, text="Server:").grid(row=6, sticky=tk.E)
        self.ipaddress= ttk.Combobox(self, textvariable=self.server, values=self.server_list, width=39)
        self.ipaddress.current(0)
        self.ipaddress.bind("<<ComboboxSelected>>", self.servercalback)
        self.ipaddress.grid(row=6, column=1, columnspan=2, sticky=tk.W)
        self.servercalback()    #update current displayed map (if enabled)
        
        self.port= ttk.Combobox(self, textvariable=self.server_port, values=self.port_list, width=4)
        if self.arg.port in self.port_list:
            self.port.current(self.port_list.index(self.arg.port))
        else:
            self.port_list.insert(0,self.arg.port)
            self.port.config(values=self.port_list, width=len(self.arg.port))
            self.port.current(0)
        self.port.grid(row=6, column=3, sticky=tk.W)
        
        tk.Label(self, text="Progress:").grid(row=7, sticky=tk.E)
        self.progress_bar = ttk.Progressbar(self
        ,orient="horizontal"
        ,length=325
        , mode="determinate")
        self.progress_bar.grid(row=7, column=1, columnspan=3, sticky=tk.W)
        
        tk.Label(self, text="Peak Mode:").grid(row=8, sticky=tk.E)
        self.max_mode_value = tk.StringVar()
        try:
            self.max_mode_value.set(self.max_options[arg.max_mode_index])
        except ValueError:
            self.max_mode_value.set(self.max_options[0]) # default value
        self.max_mode = tk.OptionMenu(self
         ,self.max_mode_value
         ,*self.max_options)
        self.max_mode.grid(row=8, column=1, columnspan=2, sticky=tk.W)
        
        self.reset_range_box = tk.Checkbutton(self, text="Reset Range for Upload", variable=self.reset_range)
        self.reset_range_box.grid(row=8, column=2, sticky=tk.W)
        
        self.show_message('see https://iperf.fr/iperf-servers.php for details of servers')
        
        if self.local_ip == '' and self.arg.geography:
            self.geography.set(0)
            self.show_message('Unable to get local external IP address, maps are disabled',True)
        elif self.arg.geography:
            self.map_box = tk.Checkbutton(self, text="Show Map", variable=self.geography)
            self.map_box.grid(row=8, column=3, sticky=tk.W)
        
        tk.Label(self, text="Range:").grid(row=9, sticky=tk.W)
        self.range_box = ttk.Combobox(self, textvariable=self.range, values=self.ranges, width=4)
        self.range_box.grid(row=10, column=0, rowspan=2)
        
        self.duration_scale = tk.Scale(self,width = 15 ,from_ = 10, to = 30
        ,orient = tk.HORIZONTAL
        ,label='Test Duration'
        ,variable=self.duration)
        self.duration_scale.grid(row=9, column=1, rowspan=2)
        
        self.threads_scale = tk.Scale(self,width = 15 ,from_ = 1, to = 30
        ,orient = tk.HORIZONTAL
        ,label='Threads'
        ,variable=self.threads)
        self.threads_scale.grid(row=9, column=2, rowspan=2)

        self.start_button = tk.Button(self,text = 'Start',width = 15,command = self.run_iperf)
        self.start_button.grid(row=9, column=3)
        self.quit = tk.Button(self,text = 'Quit',width = 15,command = self.quit)
        self.quit.grid(row=10, column=3)
        
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
        
    def set_control_state(self, state):
        self.ipaddress.config(state=state)
        self.port.config(state=state)
        self.max_mode.config(state=state)
        self.reset_range_box.config(state=state)
        if int(self.geography.get()) == 1:
            self.map_box.config(state=state)
        self.range_box.config(state=state)
        self.duration_scale.config(state=state)
        self.threads_scale.config(state=state)
        self.start_button.config(state=state)
        self.update_idletasks()
                    
    def is_ip_private(self,ip):
        # https://en.wikipedia.org/wiki/Private_network

        priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
        priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")

        res = priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip)
        return res is not None
        
    def write_config_file(self, file="./config.ini"):
        Config = ConfigParser.ConfigParser()
        Config.add_section('Servers')
        for ip_address, info in self.ip_info.items():
            self.ip_info[self.get_real_ip(ip_address)]['saved'] = True
            Config.set('Servers',self.get_real_ip(ip_address),json.dumps(self.ip_info[self.get_real_ip(ip_address)]))
            self.print('wrote data for %s to %s' % (self.get_real_ip(ip_address), file))
    
        #write config file
        with open(file, 'w') as cfgfile:
            Config.write(cfgfile)
                
    def read_config_file(self, file="./config.ini"):
        #read config file
        Config = ConfigParser.ConfigParser()
        try:
            Config.read(file)
            self.print('read config file')
            sections = Config.sections()
            self.print('sections: %s' % repr(sections))
            for section in sections:
                ipaddresses = Config.options(section)
                for ip_address in ipaddresses:
                    self.ip_info[ip_address] = json.loads(Config.get(section, ip_address))
                    self.print('read info for ip: %s from section: %s, %s' % (ip_address, section, file))
        except Exception as e:
            self.print("Error reading config file %s" %e)
            #self.write_config_file()
        
    def get_local_ip(self):
        try:
            if self.local_ip is not None and self.local_ip != '':
                return self.local_ip
        except:
            pass 
        grab = ['']
        url = 'http://checkip.dyndns.org'
        self.print('getting local ip address fron net service: %s' % url)
        try:
            req = urllib2.urlopen(url)
            grab = re.findall('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', req.read())
            self.print('local ip is: %s' % grab[0])
            req.close()
        except urllib2.URLError as e:
            self.print("Error: %s" % e)
        
        return grab[0]
        
    def get_real_ip(self, ip_address):
        if self.is_ip_private(ip_address):
            return self.local_ip
        else:
            return ip_address
        
    def get_ip_info(self, ip_address):
        if ip_address == '': return None
        if ip_address == self.local_ip:
            server_name = self.local_ip
        else:
            server_name = self.local_ip if self.is_ip_private(self.server.get()) else self.server.get()
        ip_address = self.get_real_ip(ip_address)
        if ip_address in self.ip_info.keys():
            return self.ip_info[ip_address]
        result = None
        url='https://ezcmd.com/apps/api_ezip_locator/lookup/GUEST_USER/-1/%s' % ip_address
        self.print('getting remote ip address info fron net service: %s' % url)
        try:
            req = urllib2.urlopen(url)
            data = req.read()
            result = json.loads(data)
            self.ip_info[ip_address] = result
            self.ip_info[ip_address]['server'] = server_name
            self.ip_info[ip_address]['map'] = {}
            self.ip_info[ip_address]['distance'] = {}
            self.ip_info[ip_address]['saved'] = False
            self.print(json.dumps(result, indent=2))
            req.close()
        except urllib2.URLError as e:
            self.print("Error: %s" % e)
        
        return result
 
    def calculate_distance(self,a, b):
        '''
        Return the distance between two points that have lat and lng as string 'lat,long'
        '''
        from math import sin, cos, sqrt, atan2, radians
        
        a = tuple(float(j) for j in a.split(","))
        b = tuple(float(j) for j in b.split(","))
        
        # approximate radius of earth in km. Use 3956 for miles
        R = 6373.0
        
        lat1 = radians(a[0])
        lon1 = radians(a[1])
        lat2 = radians(b[0])
        lon2 = radians(b[1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance
        
    def get_distance(self, ip_address):
        if ip_address == '' or self.local_ip == '': return -1
        if ip_address in self.ip_info.keys():
            if self.ip_info[ip_address]['distance'].get(self.local_ip, None) is not None:
                return self.ip_info[ip_address]['distance'][self.local_ip]
        result = -1
        self.print('get distance ip: %s' % ip_address)
        self.print('local ip: %s' % self.local_ip)
        self.print('remote ip info: %s' % repr(self.ip_info[ip_address]))
        self.print('local ip info: %s' % self.ip_info[self.local_ip])
        self.print('local co-ords: %s' % self.ip_info[self.local_ip]['ip_info']['coords'])
        self.print('remote co-ords: %s' % self.ip_info[ip_address]['ip_info']['coords'])
        try:
            result = self.calculate_distance(self.ip_info[self.local_ip]['ip_info']['coords'], self.ip_info[ip_address]['ip_info']['coords'])
            self.ip_info[ip_address]['distance'][self.local_ip] = result
        except Exception as e:
            self.print('Error: %s' % e)
        return result
            
    def get_map(self, a,b):
        '''
        get google static map of local and server locations, where a and b are strings of "lat,lng"
        return base64 encoded map suitable for saving in ini file, and displaying in tkinter label widget
        '''
        b64_data = None
        map_size = self.meter_size - 20
        a = a.replace(' ','')
        b = b.replace(' ','')
        
        if a==b:
            url = 'https://maps.googleapis.com/maps/api/staticmap?size=%sx%s&format=gif&maptype=roadmap&zoom=12&center=%s&markers=color:green%%7Clabel:L%%7C%s' % (map_size,map_size,a,a)
        else:
            c= ''
            if self.distance > 500:
                c = '&path=color:0x0000ff%%7Cweight:5%%7Cgeodesic:true%%7C%s%%7C%s' % (a,b)
            url = 'https://maps.googleapis.com/maps/api/staticmap?size=%sx%s&format=gif&maptype=roadmap&markers=color:green%%7Clabel:L%%7C%s&markers=color:red%%7Clabel:S%%7C%s%s' % (map_size,map_size,a,b,c)
        
        self.print('getting map from google: %s' % url)
        try:
            req = urllib2.urlopen(url)
            b64_data = base64.encodestring(req.read())
            req.close()
        except urllib2.URLError as e:
            self.print("Error: %s" % e)
            return None
        return b64_data

    def ping(self,host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """
        success = False
        ip_address = ''
        message = ''
        if HAVE_PING:
            try:
                result = pyping.ping(self.server.get())                # Need to be root or Administrator in Windows
                ip_address = result.destination_ip
                if result.ret_code != 0:
                    message = 'Could not ping server %s(%s)' % (self.server.get(),result.destination_ip)
                else:
                    message = 'Min = %sms, Max = %sms, Average = %sms' % (result.min_rtt, result.max_rtt, result.avg_rtt)
                    success = True
            except Exception as e:
                message='Error: %s' % e
            self.print('Ping: %s' % message)
        else:
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
                        message = result.replace('imum','').strip()
                        success = True
                    if 'unreachable' in result.lower():
                        break
                    if 'not' in result.lower():
                        break
                    if 'from' in result.lower():
                        ip_address = re.findall('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', result)[0]
                        self.print('remote ip is: %s' % ip_address)
                        
            p.terminate()
            
        return success, message, ip_address
        
    def show_message(self, message, error=False):
        if error:
            self.msg_label.config(text='Error:')
        else:
            self.msg_label.config(text='Ping:')
        self.ping_label.config(text=message)
        self.update_idletasks()
        
    def show_city_info(self, ip):
        distance_text = ''
        self.distance = self.get_distance(ip)
        if self.distance > 0:
            distance_text = ' Distance : %.2fkm' % self.distance
            self.print('distance is %.2fkm' % self.distance)
        if ip == self.local_ip:
            city_text ='Local Network'
        else:
            city_text ='%s, %s, %s.%s' % (  self.ip_info[ip]['ip_info']['city'],
                                            self.ip_info[ip]['ip_info']['region_name'],
                                            self.ip_info[ip]['ip_info']['country_name'],
                                            distance_text)

        self.geography_label.config(text=city_text)
        self.update_idletasks()
        
    def run_iperf(self):
        if self.server.get() == self.no_response:
            self.show_message('Please select/enter a vaild iperf3 server', True)
            self.update_idletasks()
            return
        self.map = None
        self.show_message('Testing', False)
        self.download_label.config(text='', width=60)
        self.upload_label.config(text='', width=60)
        self.meter.draw_bezel() #reset bezel to default
        self.set_control_state('disabled')
        self.update_idletasks()
        
        result, message, ip_address = self.ping(self.server.get())
        if not result:
            self.show_message('Could not ping server: %s' % self.server.get(), True)
            self.set_control_state('normal')
            return
        self.show_message(message)
        self.ip_address = self.get_real_ip(ip_address)    #current ip address of server (use external for private address)
        if self.ip_address not in self.ip_info.keys():
            self.get_ip_info(self.ip_address)
        self.show_city_info(self.ip_address)
        self.updategeography()
        self.update_idletasks()
        
        if len(self.run_iperf3(upload=False)) != 0 and not self.done: #if we get some results (not an error)
            if int(self.reset_range.get()) == 1:
                self.range.set(self.arg.range)  #reset range to default
            self.run_iperf3(upload=True)
            if self.server.get() not in self.server_list:
                self.server_list.append(self.server.get())
                self.ipaddress.config(values=self.server_list)
            try:
                if not self.ip_info[self.ip_address].get('saved', False):
                    self.write_config_file()
            except KeyError:
                pass
        else:
            if self.server.get() not in self.server_list:
                self.server.set(self.no_response)
        self.set_control_state('normal')
        self.update_idletasks()
        
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
        message = 'Attempting connection - Please Wait'
        if upload:
            self.upload_label.config(text=message)
        else:
            self.download_label.config(text=message)   
        self.update_idletasks()
        try:
            self.p = subprocess.Popen(iperf_command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            self.msg_label.config(text='%s:' % sys.exc_info()[0].__name__)
            self.ping_label.config(text='(%s) %s' % (self.arg.iperf_exec,e))
            print('Error in command: %s\r\n%s' % (iperf_command,e))
            return []
         
        message = 'Testing'
        if upload:
            self.upload_label.config(text=message)
        else:
            self.download_label.config(text=message)   

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
        units='bits/s'
        total = 0
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
                    self.show_message(line.strip(), True)
                    try:
                        message = 'Max = %s, Avg = %s %s' % (max(results_list), total if total != 0 else sum(results_list) / max(len(results_list), 1), units)
                    except ValueError:
                        message = ''
                    if upload:
                        self.upload_label.config(text=message)
                    else:
                        self.download_label.config(text=message)
                    break
                else:
                    if (int(self.threads.get()) > 1 and line.startswith('[SUM]')) or (int(self.threads.get()) == 1 and 'bits/sec' in line):
                        self.progress_bar["value"] += 1
                        speed = float(line.decode('utf-8').replace('[ ','[').replace('[ ','[').split()[5])
                        units = line.decode('utf-8').replace('[ ','[').replace('[ ','[').split()[6]
                        if 'receiver' in line:
                            total = speed
                            self.print("Total: %s %s" % (total, units))
                            message = 'Max = %s, Avg = %s %s' % (max(results_list), total, units)
                            if upload:
                                self.upload_label.config(text=message)
                            else:
                                self.download_label.config(text=message)
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
            
    def updategeography(self, *args):
        if int(self.geography.get()) == 1:
            if self.ip_address != '' and self.local_ip != '':
                if self.map is None:
                    if self.ip_info[self.ip_address].get('map', None) is not None:
                        self.map =  self.ip_info[self.ip_address]['map'].get(self.local_ip, None)
                        if self.map is not None: self.print('got map from dict')
                if self.map is None:
                    self.map = self.get_map(self.ip_info[self.local_ip]['ip_info']['coords'],self.ip_info[self.ip_address]['ip_info']['coords'])
                    self.ip_info[self.ip_address]['map'][self.local_ip] = self.map
                    if self.map is not None: self.print('got map from google')
                if self.map is not None:
                    self.map_gif = tk.PhotoImage(data=self.map)
                else:
                    self.map_gif = tk.PhotoImage(data=self.no_map)
            else:
                self.map_gif = tk.PhotoImage(data=self.no_map)
            self.meter.grid(row=5, column=0, columnspan=2)
            self.map_panel.config(image = self.map_gif)
            self.map_panel.image = self.map_gif
            self.map_panel.grid(row=5, column=2, columnspan=2, padx=(0, 20))
            self.update_idletasks()
        else:
            self.map_panel.grid_forget()
            self.meter.grid(row=5, column=0, columnspan=4)
            self.update_idletasks()
        
        self.update_idletasks()
        
    def servercalback(self, *args):
        #server selection changed
        #if self.local_ip == '': return
        self.print('Server has changed to: %s' % self.server.get())
        self.show_message('')
        self.download_label.config(text='')
        self.upload_label.config(text='')
        self.geography_label.config(text='')
        self.meter.max_val = 0
        server_name = self.local_ip if self.is_ip_private(self.server.get()) else self.server.get()
        for k in self.ip_info.keys(): 
            self.print('checking ip address: %s, server name: %s target: %s' % (k, self.ip_info[k].get('server', None), server_name))
            if server_name == self.ip_info[k].get('server', None):
                self.print('FOUND! ip address: %s' % k)
                self.ip_address = k
                self.show_city_info(k)
                if int(self.geography.get()) == 1:
                    if self.ip_info[k].get('map', None) is not None:
                        self.print('getting map for: %s' % k)
                        self.map = self.ip_info[k]['map'].get(self.local_ip, None)
                        if self.map is not None: self.print('got map from dict')
                self.updategeography()
                return
        #no map yet
        self.map = None
        if self.is_ip_private(self.server.get()):
            self.show_city_info(self.local_ip)
        else:
            self.ip_address = ''
        if int(self.geography.get()) == 1:
            self.show_message('No map found yet - will get map when test is run')
            self.print('no map found yet - will get map when test is run')
            self.updategeography()
        self.update_idletasks()
            
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
        self.title('Iperf3 Network Speed Meter (V %s)' % __VERSION__)
        Mainframe(self, arg=arg).grid()
        
def global_imports(modulename,shortname = None, asfunction = False):
    if shortname is None: 
        shortname = modulename
    if asfunction is False:
        globals()[shortname] = __import__(modulename)
    else:        
        globals()[shortname] = eval(modulename + "." + shortname)

def main():
    import argparse
    max_mode_choices = ['OFF', 'Track', 'Peak']
    parser = argparse.ArgumentParser(description='Iperf3 GUI Network Speed Tester')
    parser.add_argument('-I','--iperf_exec', action="store", default='iperf3', help='location and name of iperf3 executable (default=%(default)s)')
    parser.add_argument('-ip','--ip_address', action="store", nargs='*', default=['192.168.100.119'], help='default server address(\'s) can be a list (default=%(default)s)')
    parser.add_argument('-l','--local_ip', action="store", default=None, help='local public ip address, if not given, will be fetched automatically (default=%(default)s)')
    parser.add_argument('-p','--port', action="store", default='5201', help='server port (default=%(default)s)')
    parser.add_argument('-r','--range', action="store", type=int, default=10, help='range to start with in Mbps (default=%(default)s)')
    parser.add_argument('-R','--reset_range', action='store_false', help='Reset range to Default for Upload test (default = %(default)s)', default = True)
    parser.add_argument('-m','--max_mode', action='store', choices=max_mode_choices, help='Show Peak Mode (default = %(default)s)', default = max_mode_choices[2])
    parser.add_argument('-G','--geography', action='store_false', help='Show map data (default = %(default)s)', default = True)
    parser.add_argument('-D','--debug', action='store_true', help='debug mode', default = False)
    parser.add_argument('-V','--verbose', action='store_true', help='print everything', default = False)
    parser.add_argument('-v','--version', action='version',version='%(prog)s {version}'.format(version=__VERSION__))

    arg = parser.parse_args()
    if arg.verbose: arg.debug=True
    arg.max_mode_index = max_mode_choices.index(arg.max_mode)
    
    App(arg).mainloop()

    
if __name__ == "__main__":
    main()