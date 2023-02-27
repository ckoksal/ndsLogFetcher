#   AUTHOR : Cagri Koksal - cagri.koksal@nokia.com
#   Date   : 25.01.2019
#   Version : 1.05
#   
#   .04 - pgw log entries are sorted in ascending order.
#       - text box popup menu added for select/copy/cut/paste
#   .05 - network_complete.xml parsed to create the bds,rds,pgw lists
#       - replace checkbox with radiobuttons
#   .06 - parse network.xml file to create pgw and dsa list
#       - commit to git repo
############################################################################################
import tkinter, sys, paramiko, threading, os, sys
import xml.etree.ElementTree as ET
from datetime import datetime
############################################################################################
#self should be the first arguement of all methods in a class
class ndsconfig:
    dsaList = {}
    pgwList = []

    def parseNetworkXML(self,tpdfile):
        xmltree = ET.parse(tpdfile)
        root=xmltree.getroot()

        dsaList = {}
        pgwList = {}

        self.dsaList = {}
        self.pgwList = []

        for child in root.findall('server'):
            if (child.attrib['ComponentTPDName']=='BE-DS'):
                try:
                    nodes = list(dsaList[child.attrib['Triplet']])
                except:
                    nodes = []
                nodes.append(child.attrib['CoreLanIP_1__1'])
                dsaList[child.attrib['Triplet']] = nodes
            elif (child.attrib['ComponentTPDName']=='PGW'):
                try:
                    nodes = list(pgwList[child.attrib['Triplet']])                   
                except:
                    nodes = []
                nodes.append(child.attrib['CoreLanIP_1__1'])
                pgwList[child.attrib['Triplet']] = nodes
            else:
                pass

        for key in list(pgwList.keys()):
            for val in pgwList[key]:
                self.pgwList.append(val)

        for key in list(dsaList.keys()):
            for val in dsaList[key]:
                self.dsaList[key] = val
###########
    def setall(self,target):
        self.target=target
        if self.target=="test":
            self.parseNetworkXML(r"test_network_complete.xml")
            self.pwdList={'provgw':'siemens' , 'oamsys':'siemens' , 'sdfrun':'sdfrun1' , 'sdfrun_os':'siemens'}
        elif self.target=="live":
            self.parseNetworkXML(r"network_complete.xml")
            self.pwdList={'provgw':'pr0vgwVF_TR!1' , 'oamsys':'0am5VF5y_tr!2' , 'sdfrun':'5dfrun9' , 'sdfrun_os':'5dfrunVFTR_!1'}
        else:
            return

    def __init__(self,target):
        self.setall(target)
############################################################################################
class fetchData(threading.Thread):
    contents=[]
    def __init__(self):
        threading.Thread.__init__(self)
    # open a list box containing log files, select and scan
    def scanSelectedFiles(self,window,lb,filetype):
        selection=lb.curselection()
        
        if filetype=="journal":
            self.journalFiles=[]
            for i in selection:
                startindex=lb.get(i).find("journal")
                self.journalFiles.append(lb.get(i)[startindex:].strip("\\n"))
        if filetype=="pgw":
            self.pgwFiles=[]
            for i in selection:
                startindexforkey=lb.get(i).find("||")
                startindexforvalue=lb.get(i).find("/opt")
                pgwip=lb.get(i)[:startindexforkey]
                filename=lb.get(i)[startindexforvalue:].strip("\\n")
                #print(pgwip+":"+filename)
                self.pgwFiles.append(pgwip+":"+filename)      
        window.destroy()        
            
    #def submitCallBack2(self,window):
    #    window.destroy()
    def filterlistbox(self,lb,ftext):
        self.contents=lb.get(0,"end")
        lb.delete(0,"end")
        for entry in self.contents:
            if ftext in entry:
                lb.insert("end",entry)
                
    def refreshlistbox(self,lb,contents):
        lb.delete(0,"end")
        for entry in contents:
            lb.insert("end",entry)
    
    def filelistbox(self,filelist,filetype):
        newtop=tkinter.Tk()
        # define instance variables
        lb=tkinter.Listbox(newtop,width=80,height=25,selectmode="extended")
        Sy = tkinter.Scrollbar(newtop,orient="vertical",command=lb.yview)
        Sx = tkinter.Scrollbar(newtop,orient="horizontal",command=lb.xview)
        Sy.pack(side="right", fill="y")
        Sx.pack(side="bottom",fill="x")
        lb.pack(fill="both",expand=1)

        bt=tkinter.Button(newtop, text="Scan selected files", command=lambda: self.scanSelectedFiles(newtop,lb,filetype))
        slb=tkinter.Button(newtop, text="Filter      ", command=lambda: self.filterlistbox(lb,sen.get()))
        sen=tkinter.Entry(newtop, bd=3)
        rst=tkinter.Button(newtop, text="Reset Filter ", command=lambda: self.refreshlistbox(lb,self.contents))
        #sen.bind("<Return>",self.key(event,lb))
        slb.pack(side="left")
        sen.pack(side="left")
        rst.pack(side="left")
        bt.pack(side="right")
        #bt2.pack(side="left")
        lb.configure(yscrollcommand=Sy.set,xscrollcommand=Sx.set)
        if filetype=="journal":
            newtop.title("List of Journal Files")
            for j in range(0,len(filelist)):
                 filelist[j]=filelist[j].strip('\n')
                 lb.insert(j,filelist[j])
        if filetype=="pgw":
            newtop.title("List of PGW Log Files")
            for pgw in filelist.keys():
                 for logfile in filelist[pgw]:
                     lb.insert("end",pgw+"||"+logfile.strip('\n'))
                 
        newtop.mainloop()

    # function to return date as time stamp    
    def dateastimestamp(self,line):
        ts=datetime.strptime(line[0:23],"%Y-%m-%d %H:%M:%S,%f").timestamp()
        return ts

    # thread main code
    def run(self):
        
        if C1var.get()==1:
            pgwFiles={}
           
            for j in range(0,len(ndscfg.pgwList)):
                command='ls -lt /opt/provgw/tomcat/instance*/logs/command_logs/provgw-spml_command.log* --time-style=long-iso'
                result=remoteCommand(ndscfg.pgwList[j],"provgw",ndscfg.pwdList['provgw'],command)
                pgwFiles.update({ndscfg.pgwList[j]:result})
            self.filelistbox(pgwFiles,"pgw")
            pgwFiles=self.pgwFiles
            result=[]
            for logfile in pgwFiles:
                pgwhost=logfile[:logfile.find(":")]
                pgwlogfile=logfile[logfile.find("/opt"):]
                T1.insert("end","Scanning provisioning log file {} on {}\n".format(pgwlogfile,pgwhost))
                T1.see("end")
                command='zgrep  "DEFAULT <spml:" '+pgwlogfile+' | grep -E "'+E1.get()+'|'+E2.get()+'|'+E3.get()+'"'
                result=result+remoteCommand(pgwhost,"provgw",ndscfg.pwdList['provgw'],command)
            T1.insert("end","Finished scanning pgw log files...\n")
            printResult(sorted(result,key = self.dateastimestamp))      
        elif C1var.get()==2:
            uuid=E3.get()
            dsaId=E0.get()
            command="ls -lt --time-style=long-iso /opt/sdf/backup/journal/"
            print(ndscfg.dsaList[dsaId])
            journalFiles=remoteCommand(ndscfg.dsaList[dsaId],"sdfrun",ndscfg.pwdList['sdfrun_os'],command)
            #print(journalFiles)
            self.filelistbox(journalFiles,"journal")
            journalFiles=self.journalFiles
            
            for j in range(0,len(journalFiles)):
                 journalFiles[j]=journalFiles[j].strip('\n')
                 T1.insert("end","Scanning journal file {} on {}\n".format(journalFiles[j],ndscfg.dsaList[dsaId]))
                 T1.see("end")
                 command='jrep -j '+journalFiles[j]+' -n ".*uid='+ uuid+',ds=SUBSCRIBER,o=DEFAULT,dc=C-NTDB"'
                 result=remoteCommand(ndscfg.dsaList[dsaId],"sdfrun",ndscfg.pwdList['sdfrun_os'],command)
                 printResult(result)
            T1.insert("end","Finished scanning journal files...")
        elif C1var.get()==3:
            if E1.get()!="":
                command='ldapsearch -h localhost -p 16611 -D cn=sdfrun -w '+ndscfg.pwdList['sdfrun']+  ' -b "msisdn='+E1.get()+',dc=msisdn,dc=c-ntdb" -a always -o ldif-wrap=no masteredby'
            elif E2.get()!="":
                command='ldapsearch -h localhost -p 16611 -D cn=sdfrun -w '+ndscfg.pwdList['sdfrun']+  ' -b "imsi='+E2.get()+',dc=imsi,dc=c-ntdb" -a always -o ldif-wrap=no -o ldif-wrap=no'
            else:
                return
            
            result=remoteCommand(ndscfg.dsaList['3'],"oamsys",ndscfg.pwdList['oamsys'],command)    
            
            #find master dsa id
            startindex=str(result).find("masteredBy: ")+len("masteredBy: ")
            dsaId=str(result)[startindex:startindex+4]
            dsaId=dsaId.strip("\\n'")
            E0.delete("0","end")
            E0.insert("end",dsaId)
            # find imsi
            startindex=str(result).find("imsi=")+len("imsi=")
            imsi=str(result)[startindex:startindex+15]
            E2.delete("0","end")
            E2.insert("end",imsi)
            # find msisdn
            startindex=str(result).find("msisdn=")+len("msisdn=")
            msisdn=str(result)[startindex:startindex+12]
            E1.delete("0","end")
            E1.insert("end",msisdn)           
            #find uid
            startindex=str(result).find("uid=")+len("uid=")
            endindex=str(result)[startindex:].find(",")
            uid=str(result)[startindex:startindex+endindex]
            E3.delete("0","end")
            E3.insert("end",uid)
            # search with imsi or msisdn without masteredby option
            command=command.strip("masteredby")
            result=remoteCommand(ndscfg.dsaList['3'],"oamsys",ndscfg.pwdList['oamsys'],command)
            printResult(result)
        else:
            return


############################################################################################
def printResult(result):
    for line in result:
        T1.insert("end",line)
        T1.see("end")
#############################################################################################
def clearCallBack():
   T1.delete("1.0","end")
   E0.delete("0","end")
   E1.delete("0","end")
   E2.delete("0","end")
   E3.delete("0","end")
   E4.delete("0","end")

#############################################################################################
def exportCallBack():
    with open(E1.get()+"_output.txt", "w") as text_file:
        text_file.write(T1.get("1.0","end"))
#############################################################################################     
def submitCallBack():
    #instantiate new thread
    newThread = fetchData()
    newThread.start()
#############################################################################################
def selectTarget():
    ndscfg.setall(targetSys.get())
#############################################################################################
def selectAll(event):
    event.widget.tag_add("sel","1.0","end")   
    
def copySelection():
    top.clipboard_clear()
    top.clipboard_append(T1.selection_get())

def cutSelection():
    selrange=T1.tag_ranges("sel")
    top.clipboard_clear()
    top.clipboard_append(T1.selection_get())
    T1.delete(selrange[0],selrange[1])

def pasteClipboard():
    T1.insert("insert",top.clipboard_get())

def popupMenu(event):
    popup = tkinter.Menu(top,tearoff=0)
    popup.add_command(label="Copy",command=copySelection)
    popup.add_command(label="Cut",command=cutSelection)
    popup.add_command(label="Paste",command=pasteClipboard)
    popup.add_separator()
    # just to show that event can be passed as an arguement with lamda, otherwise, once right button clicked selectAll called
    popup.add_command(label="Select All",command=lambda: selectAll(event))
    popup.tk_popup(event.x_root,event.y_root)
    
#############################################################################################
def remoteCommand(targetHost,username,password,command):
    port=22
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
        client.connect(targetHost, port=port, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        mylines=stdout.readlines()
        #print(mylines)
    finally:
        client.close()
    return mylines
###############################################################################################
def findText():
    matchindex="_"
    startindex="1.0"
    for tag in T1.tag_names():
        #print(tag)
        T1.tag_remove("search","1.0","end")
    
    T1.tag_configure("search", background='yellow')
    if (searchText.get()!=""):
        while (1):
            matchindex=T1.search(searchText.get(),startindex,"end")
            if (matchindex!=""):
                startindex="%s+%s c" %(matchindex,len(searchText.get()))
                T1.tag_add("search", matchindex, "%s + %sc" %(matchindex,len(searchText.get())))
                T1.yview("moveto",matchindex)
                T1.xview("moveto",matchindex)
            else:
                break

###############################################################################################
top=tkinter.Tk()
top.title("OneNDS Log Fetcher")
ndscfg=ndsconfig("test")
# frame for identifiers
F0 = tkinter.Frame(top)
F0.pack(side="top")
targetSys = tkinter.StringVar()
targetSys.set("test")
R1 = tkinter.Radiobutton(F0, text="Live NDS", variable=targetSys, value="live",command=selectTarget)
R1.pack(side="left")
R2 = tkinter.Radiobutton(F0, text="Test NDS", variable=targetSys, value="test",command=selectTarget)
R2.pack(side="left")

F1 = tkinter.Frame(top)
F1.pack(side="top")

# frame for target log type
F2 = tkinter.Frame(top)
F2.pack(side="top")

# frame for Submit Button
F3 = tkinter.Frame(top)

# frame for Text Box
F4 = tkinter.Frame(top)

# frame for Find Box
F5 = tkinter.Frame(top)

# msisdn, imsi and uid entry boxes

L1 = tkinter.Label(F1, text="MSISDN")
L1.pack(side="left")
E1 = tkinter.Entry(F1, bd=2)
E1.pack(side="left")

L2 = tkinter.Label(F1, text="IMSI")
L2.pack(side="left")
E2 = tkinter.Entry(F1, bd=2)
E2.pack(side="left")

L3 = tkinter.Label(F1, text="UID")
L3.pack(side="left")
E3 = tkinter.Entry(F1, bd=2)
E3.pack(side="left")

C0var = tkinter.IntVar()
C0 = tkinter.Checkbutton(F1, variable=C0var,text="Mastered By ")
C0.pack(side="left")

E0 = tkinter.Entry(F1)
E0.pack(side="left")

# pgw and journal entry check boxes on frame 2
C1var = tkinter.IntVar()
C2var = tkinter.IntVar()
C3var = tkinter.IntVar()

C1 = tkinter.Radiobutton(F2, variable=C1var,value=1,text="PGW Log entries")
C1.pack(side="left")
C2 = tkinter.Radiobutton(F2, variable=C1var,value=2,text="Journal Log entries")
C2.pack(side="left")
C3 = tkinter.Radiobutton(F2, variable=C1var,value=3,text="Subscriber Ldif")
C3.pack(side="left")

# submit button
B1 = tkinter.Button(F3, text="Submit", command=submitCallBack)
B1.pack(side="left")
# clear button
B2 = tkinter.Button(F3,text="Clear", command=clearCallBack)
B2.pack(side="right")
# export button
B3 = tkinter.Button(F3,text="Export", command=exportCallBack)
B3.pack(side="right")
F3.pack(side="top")           
# find entry box

searchText=tkinter.StringVar()
B4 = tkinter.Button(F5,text="Find", width=10, height=1,command=findText)
#B4.pack(side="left")
B4.grid(row=0, column=0)
E4 = tkinter.Entry(F5,textvariable=searchText, width=50)
#E4 = tkinter.Entry(F5,textvariable=searchText,validate="focusout", validatecommand=findText)
#searchText.trace_add("write",findText)
#E4.pack(side="left")
E4.grid(row=0, column=1)
# output window
# packing order is importent...otherwise the scrollbars not displayed in correct place.
T1 = tkinter.Text(F4,width=160,wrap="word")
Sy = tkinter.Scrollbar(F4,orient="vertical",command=T1.yview)
Sx = tkinter.Scrollbar(F4,orient="horizontal",command=T1.xview)

Sy.pack(side="right", fill="y")
Sx.pack(side="bottom",fill="x")

T1.configure(yscrollcommand=Sy.set,xscrollcommand=Sx.set)
T1.pack(side="top",fill="both",expand=1)
F4.pack(side="top",fill="both",expand=1)
F5.pack(side="top")


T1.bind("<ButtonPress-3>",popupMenu)

top.mainloop()

