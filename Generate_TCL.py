
class TCL_scrpt():
    def __init__(self):
        self.string = self.initString()

    def initString(self):
        string = '''
    proc DisplayErrorAndCloseConnection {socketID code APIName} {
    global tcl_argv
    if {$code == -2} {
        set error_message "$APIName ERROR => -2 : TCP timeout"
    } elseif {$code == -108} {
        set error_message "$APIName ERROR => -108 : The TCP/IP connection was closed by an administrator"
    } else {
        set code2 [catch {ErrorStringGet $socketID $code strError}]
        if {$code2 != 0} {
            set error_message "$APIName ERROR => $code - ErrorStringGet ERROR => $code2"
        } else {
            set error_message "$APIName $strError"
        }
    }
    puts stdout $error_message
    set tcl_argv(0) $error_message
    catch {TCP_CloseSocket $socketID}
    return
}

####################
set TimeOut 40
set code 0

OpenConnection $TimeOut socketID
if {$socketID == -1} {
    puts stdout "OpenConnection failed => -1"
    return
}   '''

        return string

    def move(self, group, value):
        if group is MULTI_AXIS_GROUP:
            # If we are moving a multi-axis group, then we need a value for each axis. 
            # We are only working with 2 axis right now, but this would handle any number of values
            
            # If only one int was passed, assume they wanted both axis to move to that value
            if type(value) is int: 
                value = [value, value]

            v = ""
            for num in value:
                v += f"{num} "
            value = v

        self.string += f'''
        set code [GroupMoveAbsolute $socketID "Group{group}" {value}]
        '''

    def wait(self, time_ms):
        self.string += f'''
        after {time_ms}
        '''
    
    def move_and_wait(self, group, move_value, time_ms):
        self.move(group, move_value)
        self.wait(time_ms)
    
    def home(self, group):
        self.move_and_wait(group, 0, 100)

    def write_file(self, file_name):
        import os

        with open(file_name, "w") as f:
            f.write(self.string)
            f.close()
        print(f"File written to {file_name}")

ROTATION = 1
TRANSLATION = 2
MULTI_AXIS_GROUP = 3

my_script = TCL_scrpt()

#my_script.move(TRANSLATION, 200)
#my_script.wait(1000)
#my_script.move(ROTATION, 100)
#my_script.move_and_wait(TRANSLATION, -200, 1000)

my_script.home(MULTI_AXIS_GROUP)
my_script.move(MULTI_AXIS_GROUP, [40, 100])
my_script.move_and_wait(MULTI_AXIS_GROUP, [-50, -250], 1000)
my_script.move(MULTI_AXIS_GROUP, [0,0])

my_script.write_file("multi-axis.tcl")
