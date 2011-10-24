#!/usr/bin/env python
import subprocess
import sys
import pyinotify
import pynotify
import os
import time

class OnWriteHandler(pyinotify.ProcessEvent):
    def my_init(self):
        self.extensions = ('scss', 'sass')
        pynotify.init('SassWatcher')
        self.happy = 'file://' + os.path.abspath(os.path.curdir) + '/happysass.png'
        self.sad = 'file://' + os.path.abspath(os.path.curdir) + '/sadsass.png'
        self.lastMessage = ''
        self.lastTime = time.time()

    def _run_cmd(self, path, action):
        if all(not path.endswith(ext) for ext in self.extensions):
            return
        print path, "was", action
        try:
            message = subprocess.check_output(["sass", "--update", path], stderr=subprocess.STDOUT)
            if message != self.lastMessage or time.time() - self.lastTime> 0.5:
                pynotify.Notification("Success!", message, self.happy).show()
                self.lastMessage = message
                self.lastTime = time.time()
        except subprocess.CalledProcessError, e:
            message = e.output.strip()
            if message != self.lastMessage or time.time() -self.lastTime > 0.5:
                pynotify.Notification("Error:", message, self.sad).show()
                self.lastMessage = message
                self.lastTime = time.time()

    def process_IN_MODIFY(self, event):
        self._run_cmd(event.pathname, "modified")

    def process_IN_CREATE(self, event):
        self._run_cmd(event.pathname, "created")

    # This is mostly because gedit doesn't actually modify files, it writes
        # a new one and then moved it on top of the old one
    def process_IN_MOVED_TO(self, event):
        self._run_cmd(event.pathname, "moved")

def auto_compile(path):
    wm = pyinotify.WatchManager()
    handler = OnWriteHandler()
    notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
    excl = pyinotify.ExcludeFilter(['.*(<!scss)','.*(<!sass)'])
    wm.add_watch(path, pyinotify.ALL_EVENTS, rec=True, auto_add=True, exclude_filter=excl)
    try:
        notifier.loop(daemonize=True, pid_file="/tmp/pyinotify.pid")
    except pyinotify.NotifierError, err:
        print >> sys.stderr, err

if __name__ == '__main__':
    #List of Directories to monitor
    path = [os.path.expanduser('~'), 
            '/var/www/html']

    #If you get errors about WD=-1 or the message No space left on device (ENOSPC),
    #you need to increase the number of files you can watch. See the documentation at:
    #https://github.com/seb-m/pyinotify/wiki/Frequently-Asked-Questions
    #But also try typing sysctl -n fs.inotify.max_user_watches to see your current limit.
    #To increase it, as root type: sysctl -n -w fs.inotify.max_user_watches=32768
    #To make this change permanent, edit /etc/sysctl.conf and add this to the end:
    #fs.inotify.max_user_watches=32768
    #You can, of course, use any number you'd like.
    #Alternatively, you can reduce the number of directories to monitor by making the path
    #variable (above) more specific

    # Blocks monitoring
    auto_compile(path)
